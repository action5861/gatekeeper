import requests

h = lambda *codes: ''.join(chr(code) for code in codes)

keywords = [
    {"keyword": h(0xB9C8, 0xCF00, 0xD305), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xB514, 0xC9C0, 0xD130, 0xB9C8, 0xCF00, 0xD305), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xB9C8, 0xCF00, 0xD305, 0xB300, 0xD589, 0xC0AC), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xD37C, 0xD3EC, 0xBA58, 0xC2A4, 0xB9C8, 0xCF00, 0xD305), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xBC14, 0xC774, 0xB7F4, 0xB9C8, 0xCF00, 0xD305), "priority": 1, "match_type": "broad"},
    {"keyword": "SEO", "priority": 1, "match_type": "broad"},
    {"keyword": h(0xC778, 0xD50C, 0xB974, 0xC5B4, 0xC11C, 0xB9C8, 0xCF00, 0xD305), "priority": 1, "match_type": "broad"},
    {"keyword": "SNS" + h(0xC6B4, 0xC601, 0xB300, 0xD589), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xCF58, 0xD150, 0xCE20, 0xC81C, 0xC791), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xC5B8, 0xB860, 0xD64D, 0xBCF4), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xC625, 0xC678, 0xAD11, 0xACE0), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xC131, 0xC7A5, 0xC804, 0xB7AD), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xB9C8, 0xCF00, 0xD305, 0xC804, 0xBB38, 0xAC00), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xD06C, 0xB9AC, 0xC5D0, 0xC774, 0xD2F0, 0xBE0C), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xC804, 0xBB38, 0xC9C1, 0xB9C8, 0xCF00, 0xD305), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xAD11, 0xACE0, 0xB300, 0xD589), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xCEE4, 0xBBA4, 0xB2C8, 0xD2F0, 0xB9C8, 0xCF00, 0xD305), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xD1B5, 0xD569, 0xB9C8, 0xCF00, 0xD305), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xAD11, 0xACE0, 0xBB38, 0xC758), "priority": 1, "match_type": "broad"},
    {"keyword": h(0xD0AC, 0xB2E4, 0xADF8, 0xB85C, 0xC2A4), "priority": 1, "match_type": "broad"}
]

resp = requests.put('http://localhost:8007/keywords/17', json={'keywords': keywords})
print(resp.status_code)
print(resp.text)
