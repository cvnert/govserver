from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from sqlalchemy.orm import Session

from app.schemas import AskResponse, ChatTurn, Citation, SearchResult
from app.services.llm import LLMConfigurationError, get_llm_service
from app.services.retrieval import RetrievalService

NO_RESULTS_MESSAGE = "知识库中暂未检索到相关内容，建议先执行采集任务，或缩小问题范围后重试。"


class QAService:
    def __init__(self, db: Session):
        self.db = db
        self.retrieval = RetrievalService(db)
        self.llm = get_llm_service()

    def answer(self, question: str, top_k: int = 5, history: list[ChatTurn] | None = None) -> AskResponse:
        prepared = asyncio.run(self._prepare(question=question, top_k=top_k, history=history or []))
        if not prepared["hits"]:
            return AskResponse(answer=NO_RESULTS_MESSAGE, citations=[])

        citations = self._build_citations(prepared["hits"])
        if not self.llm:
            return AskResponse(answer=self._fallback_answer(prepared), citations=citations)

        try:
            answer = asyncio.run(
                self.llm.complete(
                    self._build_answer_messages(
                        question=question,
                        rewritten_query=prepared["rewritten_query"],
                        history=history or [],
                        hits=prepared["hits"],
                    )
                )
            )
        except LLMConfigurationError:
            answer = self._fallback_answer(prepared)
        except Exception:
            answer = self._fallback_answer(prepared)

        return AskResponse(answer=answer, citations=citations)

    async def stream_answer(
        self, question: str, top_k: int = 5, history: list[ChatTurn] | None = None
    ) -> AsyncIterator[str]:
        normalized_history = history or []
        prepared = await self._prepare(question=question, top_k=top_k, history=normalized_history)
        if not prepared["hits"]:
            yield self._sse("delta", {"content": NO_RESULTS_MESSAGE})
            yield self._sse("citations", {"citations": []})
            yield self._sse("done", {})
            return

        citations = self._build_citations(prepared["hits"])
        if not self.llm:
            yield self._sse("delta", {"content": self._fallback_answer(prepared)})
            yield self._sse("citations", {"citations": [citation.model_dump() for citation in citations]})
            yield self._sse("done", {})
            return

        try:
            async for chunk in self.llm.stream(
                self._build_answer_messages(
                    question=question,
                    rewritten_query=prepared["rewritten_query"],
                    history=normalized_history,
                    hits=prepared["hits"],
                )
            ):
                yield self._sse("delta", {"content": chunk})
            yield self._sse("citations", {"citations": [citation.model_dump() for citation in citations]})
            yield self._sse("done", {})
        except LLMConfigurationError as exc:
            yield self._sse("error", {"message": str(exc)})
        except Exception as exc:
            yield self._sse("error", {"message": f"LLM request failed: {exc}"})

    async def _prepare(self, question: str, top_k: int, history: list[ChatTurn]) -> dict:
        rewritten_query = await self._rewrite_query(question, history)
        query_candidates = self._query_candidates(question, rewritten_query)
        hits = self.retrieval.search(question, limit=max(top_k * 3, 8), queries=query_candidates)
        reranked_hits = await self._rerank_hits(question=question, history=history, hits=hits, top_k=top_k)
        return {
            "rewritten_query": rewritten_query,
            "query_candidates": query_candidates,
            "hits": reranked_hits,
        }

    async def _rewrite_query(self, question: str, history: list[ChatTurn]) -> str:
        if not self.llm:
            return question

        history_lines = self._history_text(history)
        prompt = (
            "你是政务知识库检索改写器。"
            "把用户当前问题改写成更适合站内检索的短查询。"
            "保留地名、部门、主题、时间、对象。"
            "如果用户用了代词或省略，请结合历史补全。"
            "只输出一行检索词，不要解释，不要加引号。"
        )
        try:
            result = await self.llm.complete(
                [
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": f"对话历史:\n{history_lines or '无'}\n\n当前问题:\n{question}",
                    },
                ]
            )
            cleaned = result.strip().splitlines()[0].strip(" -:：\"'")
            return cleaned or question
        except Exception:
            return question

    async def _rerank_hits(
        self, question: str, history: list[ChatTurn], hits: list[SearchResult], top_k: int
    ) -> list[SearchResult]:
        if not hits:
            return []

        scored = sorted(
            hits,
            key=lambda hit: self._heuristic_rerank_score(hit, question, history),
            reverse=True,
        )
        candidates = scored[: min(len(scored), max(top_k * 2, 6))]

        if not self.llm or len(candidates) <= top_k:
            return candidates[:top_k]

        prompt_lines = []
        for index, hit in enumerate(candidates, start=1):
            prompt_lines.append(
                "\n".join(
                    [
                        f"[候选 {index}]",
                        f"标题: {hit.title}",
                        f"发布时间: {hit.publish_time or '未知'}",
                        f"来源: {hit.issuer or hit.channel or '未知'}",
                        f"摘要: {hit.snippet or '无'}",
                    ]
                )
            )

        try:
            result = await self.llm.complete(
                [
                    {
                        "role": "system",
                        "content": (
                            "你是政务搜索重排器。"
                            "请从候选资料中选择最适合回答用户问题的结果。"
                            "只输出最相关候选编号，按相关度从高到低排列，用英文逗号分隔，例如 2,5,1。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"历史:\n{self._history_text(history) or '无'}\n\n"
                            f"问题:\n{question}\n\n候选资料:\n{'\n\n'.join(prompt_lines)}"
                        ),
                    },
                ]
            )
            ordered = self._parse_rank_order(result, len(candidates))
            if ordered:
                ranked = [candidates[index] for index in ordered]
                return ranked[:top_k]
        except Exception:
            pass

        return candidates[:top_k]

    def _query_candidates(self, question: str, rewritten_query: str) -> list[str]:
        candidates: list[str] = []
        for item in [question, rewritten_query]:
            normalized = item.strip()
            if normalized and normalized not in candidates:
                candidates.append(normalized)
        return candidates

    def _heuristic_rerank_score(self, hit: SearchResult, question: str, history: list[ChatTurn]) -> int:
        corpus = " ".join(
            [
                hit.title or "",
                hit.snippet or "",
                hit.issuer or "",
                hit.channel or "",
            ]
        )
        score = 0
        for token in self._tokens(question):
            if token in hit.title:
                score += 8
            if token in corpus:
                score += max(2, len(token))

        for token in self._tokens(self._history_text(history)):
            if token in corpus:
                score += 1

        if hit.publish_time:
            score += 1
        return score

    def _build_citations(self, hits: list[SearchResult]) -> list[Citation]:
        return [
            Citation(
                id=hit.id,
                title=hit.title,
                url=hit.url,
                publish_time=hit.publish_time,
                issuer=hit.issuer or hit.channel,
                snippet=hit.snippet,
            )
            for hit in hits
        ]

    def _fallback_answer(self, prepared: dict) -> str:
        lines = [
            f"根据当前知识库检索结果，围绕“{prepared['rewritten_query']}”找到以下相关资料：",
        ]
        for index, hit in enumerate(prepared["hits"], start=1):
            lines.append(
                f"{index}. {hit.title}；发布时间：{hit.publish_time or '未知'}；来源：{hit.issuer or hit.channel or '未知'}。"
            )
        lines.append("当前回答为检索汇总结果。接入大模型后，会优先生成自然语言答案。")
        return "\n".join(lines)

    def _build_answer_messages(
        self, question: str, rewritten_query: str, history: list[ChatTurn], hits: list[SearchResult]
    ) -> list[dict[str, str]]:
        context_blocks: list[str] = []
        for index, hit in enumerate(hits, start=1):
            context_blocks.append(
                "\n".join(
                    [
                        f"[资料 {index}]",
                        f"标题: {hit.title}",
                        f"发布时间: {hit.publish_time or '未知'}",
                        f"来源: {hit.issuer or hit.channel or '未知'}",
                        f"链接: {hit.url}",
                        f"摘要: {hit.snippet or '无'}",
                    ]
                )
            )

        system_prompt = (
            "你是一个政务知识库问答助手。"
            "你只能根据给定资料回答，不要编造政策、时间、部门或数字。"
            "如果资料不足，明确说明“现有资料不足以确认”。"
            "回答使用简体中文，先直接回答，再补充要点。"
        )
        user_prompt = (
            f"对话历史:\n{self._history_text(history) or '无'}\n\n"
            f"用户当前问题:\n{question}\n\n"
            f"改写后的检索问题:\n{rewritten_query}\n\n"
            f"检索资料:\n{'\n\n'.join(context_blocks)}\n\n"
            "请严格基于这些资料回答。不要输出引用编号，前端会单独展示来源。"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _history_text(self, history: list[ChatTurn]) -> str:
        if not history:
            return ""
        trimmed = history[-6:]
        return "\n".join(
            f"{'用户' if item.role == 'user' else '助手'}: {item.content.strip()}" for item in trimmed if item.content.strip()
        )

    def _tokens(self, text: str) -> list[str]:
        if not text:
            return []
        return [token for token in RetrievalService._keyword_terms(text) if len(token) >= 2][:24]

    def _parse_rank_order(self, text: str, size: int) -> list[int]:
        ordered: list[int] = []
        for chunk in text.replace("，", ",").split(","):
            cleaned = chunk.strip()
            if not cleaned.isdigit():
                continue
            index = int(cleaned) - 1
            if 0 <= index < size and index not in ordered:
                ordered.append(index)
        return ordered

    def _sse(self, event: str, payload: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
