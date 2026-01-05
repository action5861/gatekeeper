# -*- coding: utf-8 -*-
import requests

keywords = [
    {"keyword": "마케팅", "priority": 1, "match_type": "broad"},
    {"keyword": "디지털마케팅", "priority": 1, "match_type": "broad"},
    {"keyword": "마케팅대행", "priority": 1, "match_type": "broad"},
    {"keyword": "온라인마케팅", "priority": 1, "match_type": "broad"},
    {"keyword": "인스타마케팅", "priority": 1, "match_type": "broad"},
    {"keyword": "SEO", "priority": 1, "match_type": "broad"},
    {"keyword": "검색엔진최적화", "priority": 1, "match_type": "broad"},
    {"keyword": "SNS마케팅", "priority": 1, "match_type": "broad"},
    {"keyword": "소셜미디어마케팅", "priority": 1, "match_type": "broad"},
    {"keyword": "온라인광고", "priority": 1, "match_type": "broad"},
    {"keyword": "디지털광고", "priority": 1, "match_type": "broad"},
    {"keyword": "온라인홍보", "priority": 1, "match_type": "broad"},
    {"keyword": "마케팅전략", "priority": 1, "match_type": "broad"},
    {"keyword": "브랜드마케팅", "priority": 1, "match_type": "broad"},
    {"keyword": "콘텐츠마케팅", "priority": 1, "match_type": "broad"},
    {"keyword": "광고대행", "priority": 1, "match_type": "broad"},
    {"keyword": "온라인광고대행", "priority": 1, "match_type": "broad"},
    {"keyword": "디지털광고대행", "priority": 1, "match_type": "broad"},
    {"keyword": "광고전략", "priority": 1, "match_type": "broad"},
    {"keyword": "온라인으로광고", "priority": 1, "match_type": "broad"},
]

resp = requests.put("http://localhost:8007/keywords/17", json={"keywords": keywords})
print(resp.status_code)
print(resp.text)
