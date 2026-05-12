from __future__ import annotations

import hashlib
import json
import math
import re

VECTOR_DIMENSIONS = 256
VECTOR_MODEL_NAME = "hashing-v1"

SYNONYM_GROUPS = {
    "人才补贴": [
        "人才补贴",
        "人才政策",
        "人才引进",
        "生活补助",
        "租房补贴",
        "购房补贴",
        "就业补贴",
        "高校毕业生补贴",
        "青年人才",
        "高层次人才",
    ],
    "人才": [
        "人才",
        "毕业生",
        "大学生",
        "青年",
        "高层次人才",
        "引进人才",
        "技能人才",
    ],
    "补贴": [
        "补贴",
        "补助",
        "津贴",
        "资助",
        "奖励",
        "扶持",
    ],
}


def text_to_vector(text: str, dimensions: int = VECTOR_DIMENSIONS) -> list[float]:
    tokens = _feature_tokens(text)
    if not tokens:
        return [0.0] * dimensions

    vector = [0.0] * dimensions
    for token, weight in tokens.items():
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return [0.0] * dimensions
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def dumps_vector(vector: list[float]) -> str:
    return json.dumps(vector, ensure_ascii=False, separators=(",", ":"))


def loads_vector(vector_json: str) -> list[float]:
    if not vector_json:
        return []
    return [float(item) for item in json.loads(vector_json)]


def expand_semantic_queries(query: str) -> list[str]:
    normalized = query.strip()
    if not normalized:
        return []

    candidates = [normalized]
    for key, group in SYNONYM_GROUPS.items():
        if key in normalized:
            for item in group:
                if item not in candidates:
                    candidates.append(item)

    if "人才" in normalized and "补贴" in normalized:
        for item in SYNONYM_GROUPS["人才补贴"]:
            if item not in candidates:
                candidates.append(item)

    return candidates


def _feature_tokens(text: str) -> dict[str, float]:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if not normalized:
        return {}

    features: dict[str, float] = {}

    for query in expand_semantic_queries(normalized):
        _add_feature(features, f"q:{query}", 3.5)

    words = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", normalized)
    for word in words:
        _add_feature(features, f"w:{word}", 2.0)
        for size in (2, 3, 4):
            for index in range(0, max(0, len(word) - size + 1)):
                _add_feature(features, f"g:{word[index:index + size]}", 1.0)

    stripped = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", normalized)
    for size in (2, 3):
        for index in range(0, max(0, len(stripped) - size + 1)):
            _add_feature(features, f"c:{stripped[index:index + size]}", 0.8)

    return features


def _add_feature(features: dict[str, float], token: str, weight: float) -> None:
    features[token] = features.get(token, 0.0) + weight
