#!/usr/bin/env python3
"""
사용 가능한 Gemini 모델 목록 확인 스크립트
"""
import os
from google import generativeai as genai

# API 키 설정
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

if not API_KEY.strip():
    print("❌ GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
    print("   .env 파일을 확인하거나 환경 변수를 설정해주세요.")
    exit(1)

genai.configure(api_key=API_KEY)

print("🔍 현재 API 키로 사용 가능한 모델 목록 조회 중...\n")

try:
    models = list(genai.list_models())

    if not models:
        print("❌ 사용 가능한 모델이 없습니다.")
    else:
        print("✅ 사용 가능한 모델 목록:\n")
        for m in models:
            if "generateContent" in m.supported_generation_methods:
                print(f"  👉 {m.name}")

        print("\n" + "=" * 60)
        print("💡 위 모델명 중 하나를 MODEL_NAME에 사용하세요.")
        print("=" * 60)

except Exception as e:
    print(f"❌ 모델 목록 조회 실패: {e}")
    import traceback

    traceback.print_exc()
