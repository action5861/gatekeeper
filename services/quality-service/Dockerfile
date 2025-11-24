FROM python:3.11-slim

WORKDIR /app

# shared 모듈 먼저 복사
COPY shared /app/shared

# quality-service 코드 복사
COPY quality-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY quality-service /app

EXPOSE 8006

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"] 