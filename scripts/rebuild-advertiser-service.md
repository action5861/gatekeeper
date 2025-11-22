# 광고주 서비스 재빌드 명령어

## Windows (PowerShell/CMD)

```bash
# 1. 기존 컨테이너 중지 및 제거
docker stop advertiser-service
docker rm advertiser-service

# 2. 이미지 재빌드
docker build -t advertiser-service:latest ./services/advertiser-service

# 3. 컨테이너 재시작 (docker-compose 사용)
docker-compose up -d --build advertiser-service
```

또는 한 줄로:

```bash
docker-compose up -d --build advertiser-service
```

## Linux/Mac

```bash
# 1. 기존 컨테이너 중지 및 제거
docker stop advertiser-service
docker rm advertiser-service

# 2. 이미지 재빌드
docker build -t advertiser-service:latest ./services/advertiser-service

# 3. 컨테이너 재시작 (docker-compose 사용)
docker-compose up -d --build advertiser-service
```

또는 한 줄로:

```bash
docker-compose up -d --build advertiser-service
```

## 로그 확인

```bash
docker logs -f advertiser-service
```

## API 테스트

```bash
# Health check
curl http://localhost:8007/health

# API Docs
# 브라우저에서 http://localhost:8007/docs 열기

# Settlement receipt endpoint 확인
curl http://localhost:8007/settlement-receipt/test-bid-id
```

