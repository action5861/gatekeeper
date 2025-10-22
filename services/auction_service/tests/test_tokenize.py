import pytest
from services.auction_service.main import build_tokens, _normalize


def test_normalize():
    assert _normalize("  A B C  ") == "abc"
    assert _normalize("한 글 과 공 백") == "한글과공백"
    assert _normalize("TesTing 123") == "testing123"


def test_build_tokens_korean():
    tokens = set(build_tokens("프로미스나인 앨범"))
    assert "프로미스나인앨범" in tokens  # 정규화 전체
    assert "프로미스나인" in tokens  # 공백 분리
    assert "앨범" in tokens
    assert "프로" in tokens  # 2-gram
    assert "프로미" in tokens  # 3-gram
    assert len(tokens) <= 25


def test_build_tokens_english():
    tokens = set(build_tokens("fast api"))
    assert "fastapi" in tokens
    assert "fast" in tokens
    assert "api" in tokens


def test_build_tokens_empty():
    assert build_tokens("") == []
    assert build_tokens("  ") == []
