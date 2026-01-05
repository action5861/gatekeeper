# 키워드 임베딩 일괄 생성 가이드

리앤리성형외과의 키워드 임베딩이 생성되지 않은 문제를 해결하기 위한 가이드입니다.

## 방법 1: 리앤리성형외과만 처리 (추천)

### Docker 환경에서 실행

```bash
# 스크립트를 website-analysis-service 컨테이너로 복사
docker cp backfill_riannri_embeddings.py website-analysis-service:/app/

# 실행
docker exec -it website-analysis-service python /app/backfill_riannri_embeddings.py
```

### 로컬 환경에서 실행

```bash
cd services/website-analysis-service
python ../../backfill_riannri_embeddings.py
```

## 방법 2: 모든 광고주의 임베딩 없는 키워드 처리

### Docker 환경에서 실행

```bash
docker exec -it website-analysis-service python scripts/backfill_embeddings.py
```

### 로컬 환경에서 실행

```bash
cd services/website-analysis-service
python scripts/backfill_embeddings.py
```

## 상태 확인

임베딩 상태만 확인하고 싶은 경우:

```bash
docker exec -it website-analysis-service python scripts/backfill_embeddings.py --check
```

## 환경 변수 확인

스크립트 실행 전에 다음 환경 변수가 설정되어 있는지 확인하세요:

- `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`: Gemini API 키
- `GEMINI_EMBEDDING_MODEL`: 임베딩 모델 (기본값: `models/text-embedding-004`)
- `BACKFILL_BATCH_SIZE`: 배치 크기 (기본값: 10)

## 예상 결과

스크립트 실행 후 다음과 같은 결과를 볼 수 있습니다:

```
🚀 리앤리성형외과 키워드 임베딩 일괄 생성 시작
📊 설정: BATCH_SIZE=10, MODEL=models/text-embedding-004
--------------------------------------------------
📋 찾은 광고주: 1개
   - ID: 1, 회사명: 리앤리성형외과, 사용자명: riannri
   광고주#1: 임베딩 없는 키워드 35개

📋 총 임베딩이 없는 키워드: 35개
[1/35] 광고주#1 '7포인트 자연유착' 처리 중...
  ✅ 임베딩 저장 완료 (768차원)
[2/35] 광고주#1 '눈밑지방재배치 재발' 처리 중...
  ✅ 임베딩 저장 완료 (768차원)
...
--------------------------------------------------
🎉 일괄 임베딩 생성 완료!
   ✅ 성공: 35개
   ❌ 실패: 0개
   📊 성공률: 100.0%
```

## 문제 해결

### 임베딩 생성 실패 시

1. **API 키 확인**: `GEMINI_API_KEY` 환경 변수가 올바르게 설정되어 있는지 확인
2. **네트워크 확인**: 컨테이너가 인터넷에 접근할 수 있는지 확인
3. **로그 확인**: 에러 메시지를 확인하여 원인 파악

### 스크립트를 찾을 수 없는 경우

스크립트 경로를 확인하고 올바른 경로에서 실행하세요:

```bash
# 컨테이너 내부에서 확인
docker exec -it website-analysis-service ls -la /app/scripts/
docker exec -it website-analysis-service ls -la /app/
```
