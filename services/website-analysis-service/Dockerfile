FROM python:3.11-slim

WORKDIR /app

# requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Chromium 설치 (의존성 포함)
RUN playwright install chromium --with-deps

# 애플리케이션 코드 복사
COPY . .

# 포트 8009 노출
EXPOSE 8009

# 서비스 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009"]

