from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.schemas import PolicyExtraction
from app.services.llm import get_llm_service
from app.services.retrieval import RetrievalService


class PolicyExtractionService:
    LIST_FIELDS = {
        "eligible_audience",
        "support_items",
        "application_materials",
        "application_process",
        "deadlines",
        "contact_points",
        "amounts",
    }

    def __init__(self, db: Session):
        self.db = db
        self.retrieval = RetrievalService(db)
        self.llm = get_llm_service()

    async def extract_document(self, document_id: int) -> PolicyExtraction:
        document = self.retrieval.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found.")

        base = PolicyExtraction(
            policy_name=document.title,
            issuer=document.issuer,
            publish_time=document.publish_time,
            source_url=document.url,
        )
        if not self.llm:
            base.summary = (document.summary or document.content_clean[:180]).strip()
            return base

        content = document.content_clean.strip()
        if not content:
            return base

        prompt = (
            "你是政务政策信息抽取器。"
            "请从给定正文中抽取结构化字段，并只输出 JSON。"
            "字段包括 policy_name, issuer, publish_time, location, eligible_audience, support_items, "
            "application_materials, application_process, deadlines, contact_points, amounts, summary, source_url。"
            "缺失字段返回空字符串或空数组。summary 用 120 字以内简体中文概括。"
        )
        content_excerpt = content[:6000]
        result = await self.llm.complete(
            [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"标题: {document.title}\n"
                        f"来源: {document.issuer or document.channel}\n"
                        f"发布时间: {document.publish_time}\n"
                        f"链接: {document.url}\n\n"
                        f"正文:\n{content_excerpt}"
                    ),
                },
            ]
        )
        payload = self._parse_json(result)
        payload.setdefault("policy_name", document.title)
        payload.setdefault("issuer", document.issuer)
        payload.setdefault("publish_time", document.publish_time)
        payload.setdefault("source_url", document.url)
        payload = self._normalize_payload(payload)
        return PolicyExtraction.model_validate(payload)

    def _parse_json(self, text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Extractor returned invalid JSON.")
        return json.loads(cleaned[start : end + 1])

    def _normalize_payload(self, payload: dict) -> dict:
        normalized = dict(payload)
        for field in self.LIST_FIELDS:
            value = normalized.get(field, [])
            if isinstance(value, list):
                normalized[field] = [str(item).strip() for item in value if str(item).strip()]
                continue
            if isinstance(value, str):
                parts = [
                    item.strip(" -")
                    for item in value.replace("；", "\n").replace(";", "\n").replace("，", "\n").splitlines()
                    if item.strip(" -")
                ]
                normalized[field] = parts
                continue
            normalized[field] = []
        return normalized
