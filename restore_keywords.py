# -*- coding: utf-8 -*-
import requests

keywords = [
    {"keyword": "留덉???, "priority": 1, "match_type": "broad"},
    {"keyword": "?붿??몃쭏耳??, "priority": 1, "match_type": "broad"},
    {"keyword": "留덉??낅??됱궗", "priority": 1, "match_type": "broad"},
    {"keyword": "?쇳룷癒쇱뒪留덉???, "priority": 1, "match_type": "broad"},
    {"keyword": "諛붿씠?대쭏耳??, "priority": 1, "match_type": "broad"},
    {"keyword": "SEO", "priority": 1, "match_type": "broad"},
    {"keyword": "?명뵆猷⑥뼵?쒕쭏耳??, "priority": 1, "match_type": "broad"},
    {"keyword": "SNS?댁쁺???, "priority": 1, "match_type": "broad"},
    {"keyword": "肄섑뀗痢좎젣??, "priority": 1, "match_type": "broad"},
    {"keyword": "?몃줎?띾낫", "priority": 1, "match_type": "broad"},
    {"keyword": "?μ쇅愿묎퀬", "priority": 1, "match_type": "broad"},
    {"keyword": "?깆옣?꾨왂", "priority": 1, "match_type": "broad"},
    {"keyword": "留덉??낆쟾臾멸?", "priority": 1, "match_type": "broad"},
    {"keyword": "?щ━?먯씠?곕툕", "priority": 1, "match_type": "broad"},
    {"keyword": "?꾨Ц吏곷쭏耳??, "priority": 1, "match_type": "broad"},
    {"keyword": "愿묎퀬???, "priority": 1, "match_type": "broad"},
    {"keyword": "而ㅻ??덊떚留덉???, "priority": 1, "match_type": "broad"},
    {"keyword": "?듯빀留덉???, "priority": 1, "match_type": "broad"},
    {"keyword": "愿묎퀬臾몄쓽", "priority": 1, "match_type": "broad"},
    {"keyword": "?⑤떎洹몃줈??, "priority": 1, "match_type": "broad"}
]

resp = requests.put('http://localhost:8007/keywords/17', json={'keywords': keywords})
print(resp.status_code)
print(resp.text)
