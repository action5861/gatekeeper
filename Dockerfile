# 1. 의존성 설치 및 빌드 단계
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# docker-compose.yml의 환경 변수를 빌드 시에 사용
ARG ANALYSIS_SERVICE_URL
ARG AUCTION_SERVICE_URL
ARG PAYMENT_SERVICE_URL
ARG VERIFICATION_SERVICE_URL
ARG USER_SERVICE_URL
ARG QUALITY_SERVICE_URL
RUN npm run build

# 2. 프로덕션 실행 단계
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"] 