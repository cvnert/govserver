from __future__ import annotations

import re


def split_document_chunks(text: str, max_chars: int = 420) -> list[str]:
    normalized = (text or "").strip()
    if not normalized:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n+", normalized) if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            for sentence in _split_long_paragraph(paragraph, max_chars=max_chars):
                current = _append_chunk(chunks, current, sentence, max_chars=max_chars)
            continue

        current = _append_chunk(chunks, current, paragraph, max_chars=max_chars)

    if current:
        chunks.append(current)
    return chunks


def _append_chunk(chunks: list[str], current: str, part: str, max_chars: int) -> str:
    if not current:
        return part
    candidate = f"{current}\n{part}"
    if len(candidate) <= max_chars:
        return candidate
    chunks.append(current)
    return part


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    segments = [item.strip() for item in re.split(r"(?<=[。！？；;])", paragraph) if item.strip()]
    if not segments:
        return [paragraph]

    chunks: list[str] = []
    current = ""
    for segment in segments:
        if len(segment) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for index in range(0, len(segment), max_chars):
                chunks.append(segment[index : index + max_chars])
            continue
        current = _append_chunk(chunks, current, segment, max_chars=max_chars)

    if current:
        chunks.append(current)
    return chunks
