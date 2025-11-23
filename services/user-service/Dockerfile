FROM python:3.11-slim

WORKDIR /app

# shared 모듈 먼저 복사
COPY shared /app/shared

# user-service 코드 복사
COPY user-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY user-service /app

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"] 