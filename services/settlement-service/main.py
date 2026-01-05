from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, Field
from typing import List, Literal, Optional
from datetime import datetime
import random
import uuid
from jose import JWTError, jwt
from database import (
    database,
    connect_to_database,
    disconnect_from_database,
)
import os
import re
import html

app = FastAPI(title="Settlement Service", version="1.0.0")

# SLA Tier Rules Configuration
SLA_TIER_RULES = {
    "standard": {"partial_min": 10.0, "pass_min": 20.0},
    "deep": {"partial_min": 30.0, "pass_min": 60.0},
    "booster": {"partial_min": 60.0, "pass_min": 90.0},
}


# 🚀 시작 이벤트
@app.on_event("startup")
async def startup():
    await connect_to_database()
    # Ensure required columns exist
    try:
        await database.execute(
            """
            ALTER TABLE transactions ADD COLUMN IF NOT EXISTS bid_id TEXT;
            """
        )
        await database.execute(
            """
            ALTER TABLE transactions ADD COLUMN IF NOT EXISTS secondary_reward NUMERIC;
            """
        )
        await database.execute(
            """
            ALTER TABLE transactions ADD COLUMN IF NOT EXISTS settlement_decision TEXT;
            """
        )
        await database.execute(
            """
            ALTER TABLE settlements ADD COLUMN IF NOT EXISTS dwell_time NUMERIC;
            """
        )
        await database.execute(
            """
            ALTER TABLE settlements ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;
            """
        )
        await database.execute(
            """
            ALTER TABLE transactions ADD COLUMN IF NOT EXISTS target_sla_tier TEXT DEFAULT 'standard';
            """
        )
        # TODO: Verify column name 'balance' - add advertiser balance column if it doesn't exist
        await database.execute(
            """
            ALTER TABLE advertisers ADD COLUMN IF NOT EXISTS balance DECIMAL(10,2) DEFAULT 0.00;
            """
        )
        # Ensure withdrawal_requests table exists (create if not exists via migration)
        await database.execute(
            """
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            """
        )
    except Exception as e:
        print(f"⚠️ Schema ensure failed (non-fatal): {e}")


# 🛑 종료 이벤트
@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_database()


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 입력값 검증 함수들
def sanitize_input(value: str, is_url: bool = False) -> str:
    """XSS 방지를 위한 입력값 이스케이핑"""
    if not isinstance(value, str):
        return str(value)

    value = value.strip()

    # URL인 경우 특수 문자 보존
    if is_url:
        # URL에서 허용되는 특수 문자들을 보존
        # : / ? & = # 등은 URL에서 필수이므로 이스케이프하지 않음
        return value

    # 일반 텍스트는 HTML 이스케이프 적용
    return html.escape(value)


def validate_sql_injection(value: str) -> bool:
    """SQL Injection 방지를 위한 검증"""
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(--|#|/\*|\*/)",
        r"(\b(WAITFOR|DELAY)\b)",
        r"(\b(BENCHMARK|SLEEP)\b)",
    ]

    value_upper = value.upper()
    for pattern in sql_patterns:
        if re.search(pattern, value_upper, re.IGNORECASE):
            return False
    return True


# Pydantic 모델
class Transaction(BaseModel):
    id: str = Field(..., max_length=100)
    query: str = Field(..., max_length=500)
    buyerName: str = Field(..., max_length=100)
    primaryReward: int = Field(..., ge=0, le=1000000)
    secondaryReward: Optional[float] = None  # 소수점 보존을 위해 float로 변경
    settlementDecision: Optional[str] = None
    status: str = Field(..., max_length=50)
    timestamp: str = Field(..., max_length=50)

    @validator("id")
    def validate_id(cls, v):
        v = sanitize_input(v)
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "거래 ID는 영문, 숫자, 언더스코어, 하이픈만 사용 가능합니다"
            )
        if not validate_sql_injection(v):
            raise ValueError("거래 ID에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("query")
    def validate_query(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("검색어에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("buyerName")
    def validate_buyer_name(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("구매자명에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("status")
    def validate_status(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("상태에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("timestamp")
    def validate_timestamp(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("타임스탬프에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class RewardRequest(BaseModel):
    query: str = Field(..., max_length=500)
    buyerName: str = Field(..., max_length=100)
    amount: int = Field(..., ge=0, le=1000000)
    bidId: Optional[str] = None

    @validator("query")
    def validate_query(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("검색어에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("buyerName")
    def validate_buyer_name(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("구매자명에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class RewardResponse(BaseModel):
    success: bool
    message: str = Field(..., max_length=500)
    amount: Optional[int] = Field(None, ge=0, le=1000000)
    transactionId: Optional[str] = Field(None, max_length=100)
    transaction: Optional[Transaction] = None
    error: Optional[str] = Field(None, max_length=100)

    @validator("message")
    def validate_message(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("메시지에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("transactionId")
    def validate_transaction_id(cls, v):
        if v is None:
            return v
        v = sanitize_input(v)
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "거래 ID는 영문, 숫자, 언더스코어, 하이픈만 사용 가능합니다"
            )
        if not validate_sql_injection(v):
            raise ValueError("거래 ID에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("error")
    def validate_error(cls, v):
        if v is None:
            return v
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("에러 코드에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class TransactionsResponse(BaseModel):
    transactions: List[Transaction]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)


class AwardRequest(BaseModel):
    userId: int
    bidId: str
    type: str  # "PLATFORM" | "ADVERTISER"
    amount: int
    reason: str  # "click"


# JWT 설정
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
security = HTTPBearer()


# JWT 디코딩 함수
async def get_user_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """JWT 토큰에서 사용자 ID 추출"""
    try:
        print(f"🔍 JWT Token received: {credentials.credentials[:20]}...")
        print(f"🔍 SECRET_KEY: {SECRET_KEY[:10]}...")

        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=(
                os.getenv("JWT_AUDIENCE", "digisafe-client")
                if os.getenv("JWT_AUDIENCE")
                else None
            ),
            issuer=(
                os.getenv("JWT_ISSUER", "digisafe-api")
                if os.getenv("JWT_ISSUER")
                else None
            ),
            options={
                "require_exp": True,
                "verify_aud": bool(os.getenv("JWT_AUDIENCE")),
                "verify_iss": bool(os.getenv("JWT_ISSUER")),
            },
        )
        print(f"🔍 JWT Payload: {payload}")

        email = payload.get("sub")
        if email is None:
            print("❌ No email in JWT payload")
            raise HTTPException(status_code=401, detail="Invalid token")

        # 이메일로 사용자 ID 조회
        user = await database.fetch_one(
            "SELECT id FROM users WHERE email = :email", {"email": email}
        )
        if not user:
            print(f"❌ User not found for email: {email}")
            raise HTTPException(status_code=401, detail="User not found")

        print(f"✅ User found: {user['id']} for email: {email}")
        return user["id"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# 메모리 내 거래 내역 저장소 (실제로는 데이터베이스 사용)
# 이제 PostgreSQL에서 데이터를 가져옵니다


@app.post("/reward", response_model=RewardResponse)
async def process_reward(
    request: RewardRequest, user_id: int = Depends(get_user_id_from_token)
):
    """🔥 JWT에서 실제 사용자 ID 추출하여 거래 생성"""
    try:
        print(f"🎯 Payment API called for user {user_id}: {request.dict()}")

        # 보상 지급 시뮬레이션 (100% 성공률로 임시 변경)
        is_success = True  # random.random() > 0.1 대신 True로 고정

        if is_success:
            # 새로운 거래 내역 생성
            new_transaction = Transaction(
                id=f"txn_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
                query=request.query or "Unknown Search",
                buyerName=request.buyerName or "Unknown Buyer",
                primaryReward=request.amount,
                secondaryReward=None,
                settlementDecision=None,
                status="SLA_PENDING",  # 🔥 변경: 일관된 대기 상태
                timestamp=datetime.now().isoformat(),
            )

            print(
                f"💾 Creating transaction for user {user_id}: {new_transaction.dict()}"
            )

            # PostgreSQL에 거래 내역 저장 (실제 사용자 ID 사용)
            query = """
            INSERT INTO transactions (id, user_id, query_text, buyer_name, primary_reward, status, bid_id) 
            VALUES (:id, :user_id, :query_text, :buyer_name, :primary_reward, :status, :bid_id)
            """
            await database.execute(
                query,
                {
                    "id": new_transaction.id,
                    "user_id": user_id,  # 🔥 실제 JWT에서 추출한 사용자 ID!
                    "query_text": new_transaction.query,
                    "buyer_name": new_transaction.buyerName,
                    "primary_reward": new_transaction.primaryReward,
                    "status": new_transaction.status,
                    "bid_id": request.bidId,
                },
            )

            print(f"✅ Transaction saved for user {user_id}: {new_transaction.id}")

            return RewardResponse(
                success=True,
                message=f"즉시 보상 {request.amount}원이 지급되었습니다!",
                amount=request.amount,
                transactionId=new_transaction.id,
                transaction=new_transaction,
                error=None,
            )
        else:
            return RewardResponse(
                success=False,
                message="보상 지급 중 오류가 발생했습니다. 다시 시도해주세요.",
                amount=None,
                transactionId=None,
                transaction=None,
                error="PAYMENT_ERROR",
            )

    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        print(f"❌ Payment API error: {e}")
        print(f"❌ Full traceback: {error_traceback}")

        # user_id가 정의되지 않았을 수 있으므로 안전하게 처리
        user_info = f"user {user_id}" if "user_id" in locals() else "unknown user"
        print(f"❌ Error occurred for {user_info}")

        return RewardResponse(
            success=False,
            message="서버 오류가 발생했습니다.",
            amount=None,
            transactionId=None,
            transaction=None,
            error="SERVER_ERROR",
        )


@app.get("/transactions", response_model=TransactionsResponse)
async def get_transactions(user_id: int = Depends(get_user_id_from_token)):
    """거래 내역을 조회합니다. (로그인 사용자만)"""
    try:
        # PostgreSQL에서 거래 내역 조회 (user_id 필터 추가, 소수점 보존)
        transactions_data = await database.fetch_all(
            """
            SELECT t.id,
                   t.query_text AS query,
                   t.buyer_name AS "buyerName",
                   t.primary_reward AS "primaryReward",
                   COALESCE(t.secondary_reward, s.payable_amount) AS "secondaryReward",
                   COALESCE(t.settlement_decision, s.verification_decision) AS "settlementDecision",
                   COALESCE(t.settlement_decision, s.verification_decision, t.status) AS status,
                   t.created_at AS timestamp
            FROM transactions t
            LEFT JOIN LATERAL (
              SELECT verification_decision, payable_amount
              FROM settlements s
              WHERE s.trade_id = COALESCE(t.bid_id, t.id)
              ORDER BY created_at DESC
              LIMIT 1
            ) s ON TRUE
            WHERE t.user_id = :user_id
            ORDER BY t.created_at DESC
            """,
            values={"user_id": user_id},
        )

        # Pydantic 모델로 변환 (소수점 보존: float 그대로 사용)
        transactions = [
            Transaction(
                id=row["id"],
                query=row["query"],
                buyerName=row["buyerName"],
                primaryReward=int(row["primaryReward"]),
                secondaryReward=(
                    float(row["secondaryReward"])
                    if row["secondaryReward"] is not None
                    else None
                ),
                settlementDecision=(
                    row["settlementDecision"]
                    if row["settlementDecision"] is not None
                    else None
                ),
                status=row["status"],
                timestamp=(
                    row["timestamp"].isoformat()
                    if row["timestamp"]
                    else datetime.now().isoformat()
                ),
            )
            for row in transactions_data
        ]

        print(f"GET transactions called for user {user_id}, count: {len(transactions)}")
        return TransactionsResponse(
            transactions=transactions,
            total=len(transactions),
            page=1,
            limit=len(transactions),
        )
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch transactions: {str(e)}"
        )


@app.post("/award")
async def award(request: AwardRequest):
    """클릭 적립 처리 (PLATFORM 및 ADVERTISER 모두 지원)"""
    try:
        print(f"🎯 Award request: {request.dict()}")

        # 1. 광고주 ID 조회 (ADVERTISER 타입인 경우)
        advertiser_id = None
        if request.type == "ADVERTISER":
            # bid_id에서 광고주 ID 추출 시도
            try:
                if request.bidId.startswith("bid_real_"):
                    parts = request.bidId.split("_")
                    if len(parts) >= 3:
                        advertiser_id = int(parts[2])
            except (ValueError, IndexError):
                advertiser_id = None

        # 2. 거래 내역 생성
        transaction_id = f"TXN_{request.bidId}_{int(datetime.now().timestamp())}"

        insert_query = """
            INSERT INTO transactions (
                id, user_id, bid_id, advertiser_id, amount, source, reason, status, created_at
            ) VALUES (
                :transaction_id, :user_id, :bid_id, :advertiser_id, :amount, :source, :reason, 'completed', CURRENT_TIMESTAMP
            )
        """

        await database.execute(
            insert_query,
            {
                "transaction_id": transaction_id,
                "user_id": request.userId,
                "bid_id": request.bidId,
                "advertiser_id": advertiser_id,
                "amount": request.amount,
                "source": request.type,
                "reason": request.reason,
            },
        )

        print(f"✅ Transaction created: {transaction_id}")

        # 3. user-service에 거래 알림 (선택적)
        try:
            import httpx

            user_tx_url = "http://user-service:8005/transactions/record"
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    user_tx_url,
                    json={
                        "userId": request.userId,
                        "transactionId": transaction_id,
                        "amount": request.amount,
                        "source": request.type,
                        "reason": request.reason,
                    },
                )
            print(f"✅ User service notified")
        except Exception as e:
            print(f"⚠️ User service notification failed: {e}")
            # 알림 실패는 전체 프로세스에 영향을 주지 않음

        return {"ok": True, "transactionId": transaction_id}

    except Exception as e:
        print(f"❌ Award error: {e}")
        raise HTTPException(status_code=500, detail=f"Award error: {str(e)}")


class SettlementRequest(BaseModel):
    trade_id: str
    verification_decision: str
    metrics: Optional[dict] = None
    dwell_time: Optional[float] = None  # 체류시간 직접 전달 (선택적)


# Withdrawal/Payout Models
class WithdrawalRequest(BaseModel):
    request_amount: int = Field(
        ..., ge=10000, description="Minimum withdrawal: 10,000 Points"
    )
    bank_name: str = Field(..., min_length=1, max_length=100)
    account_number: str = Field(..., min_length=1, max_length=100)
    account_holder: str = Field(..., min_length=1, max_length=100)

    @validator("request_amount")
    def validate_request_amount(cls, v):
        if v < 10000:
            raise ValueError("Minimum withdrawal amount is 10,000 Points")
        return v

    @validator("bank_name", "account_number", "account_holder")
    def validate_bank_info(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("Invalid characters in bank information")
        return v


class WithdrawalResponse(BaseModel):
    success: bool
    message: str
    withdrawal_id: Optional[str] = None
    request_amount: Optional[int] = None
    tax_amount: Optional[int] = None
    final_amount: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[str] = None


class WithdrawalHistoryItem(BaseModel):
    id: str
    request_amount: int
    tax_amount: int
    final_amount: int
    bank_name: str
    account_number: str
    account_holder: str
    status: str
    created_at: str


class WithdrawalHistoryResponse(BaseModel):
    withdrawals: List[WithdrawalHistoryItem]
    total: int


@app.post("/settle-trade")
async def settle_trade_api(request: SettlementRequest):
    """
    Zero Risk Guarantee Settlement System
    - Tier-based SLA verification (server-side decision)
    - User payout (difference-based update)
    - Advertiser refund (for PARTIAL/FAILED SLA)
    - Budget restoration
    - All operations in single atomic transaction
    """
    try:
        print(
            f"💰 Settlement processing for trade_id: {request.trade_id}, client_decision: {request.verification_decision}"
        )

        async with database.transaction():
            # 1. Retrieve transaction with tier information
            trade = await database.fetch_one(
                """SELECT user_id, primary_reward, bid_id, status as current_status, target_sla_tier
                   FROM transactions 
                   WHERE (bid_id = :trade_id OR id = :trade_id)""",
                values={"trade_id": request.trade_id},
            )

            if not trade:
                print(f"⚠️ Trade not found: {request.trade_id}")
                return {
                    "success": False,
                    "message": "Trade not found",
                }

            # 2. Determine SLA tier (fallback to 'standard')
            tier_name = (
                trade["target_sla_tier"]
                if "target_sla_tier" in trade and trade["target_sla_tier"]
                else "standard"
            )
            if tier_name not in SLA_TIER_RULES:
                print(f"⚠️ Invalid tier '{tier_name}', using 'standard'")
                tier_name = "standard"

            tier_rules = SLA_TIER_RULES[tier_name]
            partial_min = tier_rules["partial_min"]
            pass_min = tier_rules["pass_min"]
            print(
                f"📊 SLA Tier: {tier_name} (partial_min={partial_min}s, pass_min={pass_min}s)"
            )

            # 3. Extract actual dwell time (priority: dwell_time > metrics)
            actual_dwell = 0.0
            if request.dwell_time is not None and request.dwell_time > 0:
                actual_dwell = float(request.dwell_time)
                print(f"📊 Using dwell_time from request: {actual_dwell}s")
            elif request.metrics:
                dwell_candidates = [
                    request.metrics.get("t_dwell"),
                    request.metrics.get("t_dwell_on_ad_site"),
                    request.metrics.get("dwell_time"),
                ]
                for candidate in dwell_candidates:
                    if candidate is not None and float(candidate) > 0:
                        actual_dwell = float(candidate)
                        print(f"📊 Using dwell_time from metrics: {actual_dwell}s")
                        break

            if actual_dwell <= 0:
                print(f"⚠️ No valid dwell time found, using 0s")
                actual_dwell = 0.0

            # 4. Server-side decision calculation (IGNORE client verification_decision)
            original_bid_price = float(trade["primary_reward"])

            if actual_dwell < partial_min:
                # FAILED: actual_dwell < partial_min
                final_decision = "FAILED"
                payout_ratio = 0.0
                payable_amount = 0.0
                print(f"❌ FAILED: {actual_dwell:.2f}s < {partial_min}s (ratio=0.0)")
            elif actual_dwell >= pass_min:
                # PASSED: actual_dwell >= pass_min
                final_decision = "PASSED"
                payout_ratio = 1.0
                payable_amount = original_bid_price
                print(f"✅ PASSED: {actual_dwell:.2f}s >= {pass_min}s (ratio=1.0)")
            else:
                # PARTIAL: partial_min <= actual_dwell < pass_min
                final_decision = "PARTIAL"
                # Linear interpolation: ratio = 0.5 + 0.5 * ((actual_dwell - partial_min) / (pass_min - partial_min))
                payout_ratio = 0.5 + 0.5 * (
                    (actual_dwell - partial_min) / (pass_min - partial_min)
                )
                payout_ratio = max(0.0, min(1.0, payout_ratio))  # Clamp to [0.0, 1.0]
                payable_amount = original_bid_price * payout_ratio
                print(
                    f"📈 PARTIAL: {actual_dwell:.2f}s -> ratio={payout_ratio:.2%}, payable={payable_amount:.2f}원"
                )

            # 5. Check previous settlement (for difference-based user payout)
            previous_settlement = await database.fetch_one(
                """SELECT verification_decision, payable_amount 
                   FROM settlements 
                   WHERE trade_id = :trade_id 
                   ORDER BY created_at DESC LIMIT 1""",
                values={"trade_id": request.trade_id},
            )

            previous_amount = (
                float(previous_settlement["payable_amount"])
                if previous_settlement
                else 0.0
            )
            print(f"📊 Previous settlement: {previous_amount}원")

            # 6. User payout (difference-based update)
            amount_difference = payable_amount - previous_amount
            final_status = "SETTLED" if payable_amount > 0 else "FAILED"

            if amount_difference != 0:
                await database.execute(
                    """
                    UPDATE users SET total_earnings = GREATEST(total_earnings + :diff, 0)
                    WHERE id = :user_id
                    """,
                    values={"diff": amount_difference, "user_id": trade["user_id"]},
                )
                adj = "+" if amount_difference > 0 else ""
                print(
                    f"✅ User payout: {adj}{amount_difference}원 for user_id {trade['user_id']} (new: {payable_amount}원, prev: {previous_amount}원)"
                )
            else:
                print(
                    f"ℹ️ No user balance change: {payable_amount}원 (same as previous)"
                )

            # 7. Advertiser refund (Zero Risk Guarantee) - 차액 기반 처리
            # bid_id 확인: trade.bid_id가 있으면 사용, 없으면 trade_id 자체가 bid_id일 수 있음
            bid_id = (
                trade["bid_id"]
                if "bid_id" in trade and trade["bid_id"]
                else request.trade_id
            )
            if bid_id:
                bid_info = await database.fetch_one(
                    """SELECT advertiser_id, price FROM bids WHERE id = :bid_id""",
                    values={"bid_id": bid_id},
                )

                if (
                    bid_info
                    and "advertiser_id" in bid_info
                    and bid_info["advertiser_id"]
                ):
                    advertiser_id = bid_info["advertiser_id"]
                    bid_price = float(bid_info["price"]) if "price" in bid_info else 0.0

                    # Calculate current refund amount based on SLA result
                    current_refund = 0.0
                    if final_decision == "PASSED":
                        # Full payment: no refund
                        current_refund = 0.0
                    elif final_decision == "PARTIAL":
                        # Partial: refund = original_bid_price - payable_amount
                        current_refund = original_bid_price - payable_amount
                    else:  # FAILED
                        # Failed: 100% refund
                        current_refund = original_bid_price

                    # Calculate previous refund from previous settlement
                    previous_refund = 0.0
                    if previous_settlement:
                        prev_decision = (
                            previous_settlement["verification_decision"]
                            if "verification_decision" in previous_settlement
                            else None
                        )
                        prev_payable = float(previous_settlement["payable_amount"])
                        if prev_decision == "FAILED":
                            previous_refund = original_bid_price
                        elif prev_decision == "PARTIAL":
                            previous_refund = original_bid_price - prev_payable
                        # PASSED면 previous_refund = 0.0 (이미 0으로 초기화됨)

                    # Calculate refund difference (차액 기반 환불/회수)
                    refund_difference = current_refund - previous_refund
                    print(
                        f"💰 Refund calculation: current={current_refund:.2f}원, previous={previous_refund:.2f}원, difference={refund_difference:.2f}원"
                    )

                    if refund_difference > 0:
                        # 환불 증가: 광고주에게 환불 (balance/budget 복구)
                        await database.execute(
                            """
                            UPDATE advertisers 
                            SET balance = balance + :refund
                            WHERE id = :advertiser_id
                            """,
                            values={
                                "refund": refund_difference,
                                "advertiser_id": advertiser_id,
                            },
                        )
                        await database.execute(
                            """
                            UPDATE auto_bid_settings 
                            SET daily_budget = daily_budget + :refund
                            WHERE advertiser_id = :advertiser_id
                            """,
                            values={
                                "refund": refund_difference,
                                "advertiser_id": advertiser_id,
                            },
                        )
                        print(
                            f"💰 Advertiser Refund: +{refund_difference:.2f}원 (total refund={current_refund:.2f}원) - Balance & Budget restored"
                        )
                    elif refund_difference < 0:
                        # 환불 감소: 이전 환불 회수 (balance/budget 차감)
                        await database.execute(
                            """
                            UPDATE advertisers 
                            SET balance = GREATEST(balance - :refund_recovery, 0)
                            WHERE id = :advertiser_id
                            """,
                            values={
                                "refund_recovery": abs(refund_difference),
                                "advertiser_id": advertiser_id,
                            },
                        )
                        await database.execute(
                            """
                            UPDATE auto_bid_settings 
                            SET daily_budget = GREATEST(daily_budget - :refund_recovery, 0)
                            WHERE advertiser_id = :advertiser_id
                            """,
                            values={
                                "refund_recovery": abs(refund_difference),
                                "advertiser_id": advertiser_id,
                            },
                        )
                        print(
                            f"💰 Advertiser Refund Recovery: -{abs(refund_difference):.2f}원 (previous={previous_refund:.2f}원, current={current_refund:.2f}원) - Balance & Budget adjusted"
                        )
                    else:
                        print(
                            f"💰 Advertiser Refund: No change (refund={current_refund:.2f}원, same as previous)"
                        )

                    refund_amount = current_refund  # 최종 환불 금액 (로깅용)

                    # 🔥 SSOT 통일: bids 테이블에 정산 결과 기록
                    await database.execute(
                        """
                        UPDATE bids
                           SET settlement_decision = :decision,
                               settled_amount      = :amount,
                               settled_at          = CURRENT_TIMESTAMP
                         WHERE id = :bid_id
                        """,
                        values={
                            "decision": final_decision,
                            "amount": payable_amount,
                            "bid_id": bid_id,
                        },
                    )
                    print(
                        f"✅ Updated bid: bid_id={bid_id}, decision={final_decision}, settled_amount={payable_amount:.2f}원"
                    )
                else:
                    print(
                        f"⚠️ Bid not found or no advertiser_id for bid_id={bid_id}, skipping refund"
                    )
                    refund_amount = 0.0
            else:
                print(f"⚠️ No bid_id in transaction, skipping advertiser refund")
                refund_amount = 0.0

            # 8. Update transaction status and settlement decision
            await database.execute(
                """UPDATE transactions
                       SET status = :status,
                           secondary_reward = :secondary_reward,
                           settlement_decision = :decision
                     WHERE (bid_id = :trade_id OR id = :trade_id)""",
                values={
                    "status": final_status,
                    "secondary_reward": payable_amount,
                    "decision": final_decision,
                    "trade_id": request.trade_id,
                },
            )
            print(
                f"✅ Updated transaction: status={final_status}, decision={final_decision}"
            )

            # 9. Insert settlement record
            await database.execute(
                """INSERT INTO settlements (trade_id, verification_decision, payable_amount, dwell_time)
                   VALUES (:trade_id, :decision, :amount, :dwell_time)""",
                values={
                    "trade_id": request.trade_id,
                    "decision": final_decision,
                    "amount": payable_amount,
                    "dwell_time": actual_dwell,
                },
            )
            print(
                f"✅ Settlement recorded: trade_id={request.trade_id}, decision={final_decision}, amount={payable_amount:.2f}원, refund={refund_amount:.2f}원"
            )

        return {
            "success": True,
            "trade_id": request.trade_id,
            "verification_decision": final_decision,
            "payable_amount": payable_amount,
            "final_status": final_status,
            "refund_amount": refund_amount,
            "message": f"정산 완료: {payable_amount}원 (환불: {refund_amount}원)",
        }

    except Exception as e:
        print(f"❌ Settlement error for trade_id {request.trade_id}: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"정산 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/settlement/withdraw", response_model=WithdrawalResponse)
async def request_withdrawal(
    request: WithdrawalRequest,
    user_id: int = Depends(get_user_id_from_token),
):
    """
    출금 요청을 처리합니다.
    - 최소 출금 금액: 10,000 Points
    - 원자적 트랜잭션으로 잔고 차감 및 출금 요청 기록
    """
    try:
        print(f"💸 Withdrawal request from user {user_id}: {request.dict()}")

        # Input validation is handled by Pydantic

        # No tax deduction - full amount is paid
        tax_amount = 0
        final_amount = request.request_amount

        async with database.transaction():
            # 1. Check user balance
            user = await database.fetch_one(
                "SELECT id, total_earnings FROM users WHERE id = :user_id FOR UPDATE",
                values={"user_id": user_id},
            )

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            current_balance = (
                float(user["total_earnings"]) if user["total_earnings"] else 0.0
            )

            if current_balance < request.request_amount:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Current balance: {int(current_balance)} Points, Requested: {request.request_amount} Points",
                )

            # 2. Deduct balance from users.total_earnings
            new_balance = current_balance - request.request_amount
            await database.execute(
                """
                UPDATE users 
                SET total_earnings = GREATEST(:new_balance, 0)
                WHERE id = :user_id
                """,
                values={"new_balance": new_balance, "user_id": user_id},
            )
            print(f"✅ Balance updated: {current_balance} -> {new_balance} Points")

            # 3. Insert withdrawal request record
            withdrawal_id = str(uuid.uuid4())
            await database.execute(
                """
                INSERT INTO withdrawal_requests 
                (id, user_id, request_amount, tax_amount, final_amount, bank_name, account_number, account_holder, status)
                VALUES (:id, :user_id, :request_amount, :tax_amount, :final_amount, :bank_name, :account_number, :account_holder, 'REQUESTED')
                """,
                values={
                    "id": withdrawal_id,
                    "user_id": user_id,
                    "request_amount": request.request_amount,
                    "tax_amount": tax_amount,
                    "final_amount": final_amount,
                    "bank_name": request.bank_name,
                    "account_number": request.account_number,
                    "account_holder": request.account_holder,
                },
            )
            print(f"✅ Withdrawal request created: {withdrawal_id}")

        return WithdrawalResponse(
            success=True,
            message=f"출금 요청이 접수되었습니다. {final_amount:,} Points가 지급됩니다.",
            withdrawal_id=withdrawal_id,
            request_amount=request.request_amount,
            tax_amount=tax_amount,
            final_amount=final_amount,
            status="REQUESTED",
            created_at=datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Withdrawal error for user {user_id}: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"출금 요청 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/api/settlement/withdraw/history", response_model=WithdrawalHistoryResponse)
async def get_withdrawal_history(
    user_id: int = Depends(get_user_id_from_token),
):
    """
    사용자의 출금 내역을 조회합니다.
    최신순(created_at DESC)으로 정렬됩니다.
    """
    try:
        print(f"📜 Fetching withdrawal history for user {user_id}")

        # Fetch withdrawal history from database
        withdrawals_data = await database.fetch_all(
            """
            SELECT 
                id::text as id,
                request_amount,
                tax_amount,
                final_amount,
                bank_name,
                account_number,
                account_holder,
                status,
                created_at
            FROM withdrawal_requests
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            """,
            values={"user_id": user_id},
        )

        # Convert to Pydantic models
        withdrawals = [
            WithdrawalHistoryItem(
                id=row["id"],
                request_amount=int(row["request_amount"]),
                tax_amount=int(row["tax_amount"]),
                final_amount=int(row["final_amount"]),
                bank_name=row["bank_name"],
                account_number=row["account_number"],
                account_holder=row["account_holder"],
                status=row["status"],
                created_at=(
                    row["created_at"].isoformat()
                    if row["created_at"]
                    else datetime.now().isoformat()
                ),
            )
            for row in withdrawals_data
        ]

        print(f"✅ Found {len(withdrawals)} withdrawal records for user {user_id}")
        return WithdrawalHistoryResponse(
            withdrawals=withdrawals,
            total=len(withdrawals),
        )

    except Exception as e:
        print(f"❌ Error fetching withdrawal history for user {user_id}: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"출금 내역 조회 중 오류가 발생했습니다: {str(e)}"
        )


# ============================================
# 플랫폼 정산 통계 API (관리자용)
# ============================================


class PlatformSettlementSummary(BaseModel):
    """플랫폼 정산 요약"""

    total_count: int
    total_amount: int
    advertiser_count: int
    advertiser_amount: int
    platform_count: int
    platform_amount: int
    platform_ratio: float  # 플랫폼 비율 (매칭 실패율)


class DailySettlement(BaseModel):
    """일별 정산 데이터"""

    date: str
    platform_count: int
    platform_amount: int
    advertiser_count: int
    advertiser_amount: int


class UserPlatformSettlement(BaseModel):
    """사용자별 플랫폼 정산 내역"""

    user_id: int
    username: str
    email: str
    platform_count: int
    platform_amount: int
    last_settlement_date: Optional[str]


class PlatformSettlementStatsResponse(BaseModel):
    """플랫폼 정산 통계 전체 응답"""

    summary: PlatformSettlementSummary
    daily_trend: List[DailySettlement]
    top_users: List[UserPlatformSettlement]
    period: str


@app.get("/admin/platform-settlements/stats")
async def get_platform_settlement_stats(period: str = "week"):  # day, week, month
    """
    플랫폼 정산 통계를 조회합니다.
    - 총 플랫폼 정산 건수/금액
    - 일별 추이
    - 매칭 실패 비율
    - 사용자별 플랫폼 정산 내역 (상위 20명)

    인덱스를 활용한 효율적인 쿼리로 시스템 부하 최소화
    """
    try:
        # 기간 설정 (날짜를 미리 계산)
        from datetime import timedelta

        days_map = {"day": 1, "week": 7, "month": 30}
        days = days_map.get(period, 7)
        start_date = datetime.now() - timedelta(days=days)

        # 1. 요약 통계 (인덱스 활용)
        summary_query = """
            SELECT 
                COUNT(*) as total_count,
                COALESCE(SUM(b.price), 0) as total_amount,
                COUNT(*) FILTER (WHERE b.type = 'ADVERTISER') as advertiser_count,
                COALESCE(SUM(b.price) FILTER (WHERE b.type = 'ADVERTISER'), 0) as advertiser_amount,
                COUNT(*) FILTER (WHERE b.type = 'PLATFORM') as platform_count,
                COALESCE(SUM(b.price) FILTER (WHERE b.type = 'PLATFORM'), 0) as platform_amount
            FROM bids b
            WHERE b.created_at >= :start_date
              AND b.user_id IS NOT NULL
        """
        summary_row = await database.fetch_one(
            summary_query, values={"start_date": start_date}
        )

        # None 체크
        if summary_row is None:
            summary = PlatformSettlementSummary(
                total_count=0,
                total_amount=0,
                advertiser_count=0,
                advertiser_amount=0,
                platform_count=0,
                platform_amount=0,
                platform_ratio=0.0,
            )
        else:
            total_count = summary_row["total_count"] or 0
            platform_count = summary_row["platform_count"] or 0
            platform_ratio = (
                (platform_count / total_count * 100) if total_count > 0 else 0
            )

            summary = PlatformSettlementSummary(
                total_count=total_count,
                total_amount=int(summary_row["total_amount"] or 0),
                advertiser_count=summary_row["advertiser_count"] or 0,
                advertiser_amount=int(summary_row["advertiser_amount"] or 0),
                platform_count=platform_count,
                platform_amount=int(summary_row["platform_amount"] or 0),
                platform_ratio=round(platform_ratio, 2),
            )

        # 2. 일별 추이 (최근 기간, 인덱스 활용)
        daily_query = """
            SELECT 
                DATE(b.created_at) as date,
                COUNT(*) FILTER (WHERE b.type = 'PLATFORM') as platform_count,
                COALESCE(SUM(b.price) FILTER (WHERE b.type = 'PLATFORM'), 0) as platform_amount,
                COUNT(*) FILTER (WHERE b.type = 'ADVERTISER') as advertiser_count,
                COALESCE(SUM(b.price) FILTER (WHERE b.type = 'ADVERTISER'), 0) as advertiser_amount
            FROM bids b
            WHERE b.created_at >= :start_date
              AND b.user_id IS NOT NULL
            GROUP BY DATE(b.created_at)
            ORDER BY DATE(b.created_at) DESC
            LIMIT 30
        """
        daily_rows = await database.fetch_all(
            daily_query, values={"start_date": start_date}
        )

        daily_trend = [
            DailySettlement(
                date=str(row["date"]),
                platform_count=row["platform_count"] or 0,
                platform_amount=int(row["platform_amount"] or 0),
                advertiser_count=row["advertiser_count"] or 0,
                advertiser_amount=int(row["advertiser_amount"] or 0),
            )
            for row in daily_rows
        ]

        # 3. 사용자별 플랫폼 정산 내역 (상위 20명, 페이지네이션 적용)
        users_query = """
            SELECT 
                u.id as user_id,
                u.username,
                u.email,
                COUNT(b.id) as platform_count,
                COALESCE(SUM(b.price), 0) as platform_amount,
                MAX(b.created_at) as last_settlement_date
            FROM bids b
            INNER JOIN users u ON b.user_id = u.id
            WHERE b.type = 'PLATFORM'
              AND b.created_at >= :start_date
            GROUP BY u.id, u.username, u.email
            ORDER BY platform_count DESC
            LIMIT 20
        """
        users_rows = await database.fetch_all(
            users_query, values={"start_date": start_date}
        )

        top_users = [
            UserPlatformSettlement(
                user_id=row["user_id"],
                username=row["username"],
                email=row["email"],
                platform_count=row["platform_count"],
                platform_amount=int(row["platform_amount"]),
                last_settlement_date=(
                    row["last_settlement_date"].isoformat()
                    if row["last_settlement_date"]
                    else None
                ),
            )
            for row in users_rows
        ]

        print(
            f"📊 Platform settlement stats fetched: {summary.platform_count} platform, {summary.advertiser_count} advertiser"
        )

        return PlatformSettlementStatsResponse(
            summary=summary, daily_trend=daily_trend, top_users=top_users, period=period
        )

    except Exception as e:
        print(f"❌ Platform settlement stats error: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"플랫폼 정산 통계 조회 중 오류가 발생했습니다: {str(e)}",
        )


@app.get("/admin/platform-settlements/users")
async def get_platform_settlement_users(
    page: int = 1, page_size: int = 20, period: str = "week"
):
    """
    플랫폼 정산을 받은 사용자 목록을 페이지네이션으로 조회합니다.
    시스템 부하 방지를 위해 페이지당 20건씩 조회합니다.
    """
    try:
        from datetime import timedelta

        days_map = {"day": 1, "week": 7, "month": 30}
        days = days_map.get(period, 7)
        start_date = datetime.now() - timedelta(days=days)

        offset = (page - 1) * page_size

        # 총 건수 조회 (캐싱 가능)
        count_query = """
            SELECT COUNT(DISTINCT b.user_id) as total
            FROM bids b
            WHERE b.type = 'PLATFORM'
              AND b.created_at >= :start_date
              AND b.user_id IS NOT NULL
        """
        count_row = await database.fetch_one(
            count_query, values={"start_date": start_date}
        )
        total = count_row["total"] if count_row else 0

        # 페이지네이션된 사용자 목록
        users_query = """
            SELECT 
                u.id as user_id,
                u.username,
                u.email,
                COUNT(b.id) as platform_count,
                COALESCE(SUM(b.price), 0) as platform_amount,
                MAX(b.created_at) as last_settlement_date
            FROM bids b
            INNER JOIN users u ON b.user_id = u.id
            WHERE b.type = 'PLATFORM'
              AND b.created_at >= :start_date
            GROUP BY u.id, u.username, u.email
            ORDER BY platform_count DESC
            LIMIT :page_size OFFSET :offset
        """
        users_rows = await database.fetch_all(
            users_query,
            values={"start_date": start_date, "page_size": page_size, "offset": offset},
        )

        users = [
            UserPlatformSettlement(
                user_id=row["user_id"],
                username=row["username"],
                email=row["email"],
                platform_count=row["platform_count"],
                platform_amount=int(row["platform_amount"]),
                last_settlement_date=(
                    row["last_settlement_date"].isoformat()
                    if row["last_settlement_date"]
                    else None
                ),
            )
            for row in users_rows
        ]

        return {
            "users": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    except Exception as e:
        print(f"❌ Platform settlement users error: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"사용자별 플랫폼 정산 조회 중 오류가 발생했습니다: {str(e)}",
        )


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "settlement-service",
        "database": "connected",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
