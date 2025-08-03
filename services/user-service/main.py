from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Literal, Optional
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from database import (
    database,
    User,
    UserQualityHistory,
    connect_to_database,
    disconnect_from_database,
)

app = FastAPI(title="User Service", version="1.0.0")


# 🚀 시작 이벤트
@app.on_event("startup")
async def startup():
    await connect_to_database()


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

# 보안 설정
SECRET_KEY = "a_very_secret_key_for_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# Pydantic 모델들
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class QualityHistory(BaseModel):
    name: str
    score: int


class SubmissionLimit(BaseModel):
    level: Literal["Excellent", "Good", "Average", "Needs Improvement"]
    dailyMax: int


class DashboardResponse(BaseModel):
    earnings: dict
    qualityHistory: List[QualityHistory]
    qualityStats: dict
    submissionLimit: SubmissionLimit
    dailySubmission: dict
    stats: dict
    transactions: List[dict]


class EarningsRequest(BaseModel):
    amount: int


class QualityScoreRequest(BaseModel):
    score: int
    week_label: str


class SubmissionRequest(BaseModel):
    quality_score: int


# 🔐 보안 함수들
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def calculate_dynamic_limit(quality_score: int) -> SubmissionLimit:
    base_limit = 20
    if quality_score >= 90:
        return SubmissionLimit(level="Excellent", dailyMax=base_limit * 2)
    elif quality_score >= 70:
        return SubmissionLimit(level="Good", dailyMax=base_limit)
    elif quality_score >= 50:
        return SubmissionLimit(level="Average", dailyMax=int(base_limit * 0.7))
    else:
        return SubmissionLimit(
            level="Needs Improvement", dailyMax=int(base_limit * 0.3)
        )


# JWT 인증 함수
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await database.fetch_one(
        "SELECT * FROM users WHERE email = :email", {"email": email}
    )
    if user is None:
        raise credentials_exception
    return dict(user)


# 📊 API 엔드포인트들
@app.post("/register", status_code=201)
async def register_user(user: UserCreate):
    """신규 사용자 등록"""
    try:
        # 이메일 중복 확인
        existing_user = await database.fetch_one(
            "SELECT id FROM users WHERE email = :email", {"email": user.email}
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

        # 사용자명 중복 확인
        existing_username = await database.fetch_one(
            "SELECT id FROM users WHERE username = :username",
            {"username": user.username},
        )
        if existing_username:
            raise HTTPException(
                status_code=400, detail="이미 사용 중인 사용자명입니다."
            )

        # 비밀번호 해싱
        hashed_password = get_password_hash(user.password)

        # 사용자 생성
        query = """
        INSERT INTO users (username, email, hashed_password) 
        VALUES (:username, :email, :hashed_password)
        """
        await database.execute(
            query,
            {
                "username": user.username,
                "email": user.email,
                "hashed_password": hashed_password,
            },
        )

        return {"message": "회원가입이 성공적으로 완료되었습니다."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"등록 실패: {str(e)}")


@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    """사용자 로그인 및 JWT 토큰 발급"""
    try:
        print(f"🔐 Login attempt for email: {form_data.email}")

        # 사용자 조회
        user = await database.fetch_one(
            "SELECT * FROM users WHERE email = :email", {"email": form_data.email}
        )

        print(f"👤 User found: {user is not None}")

        if not user:
            print("❌ User not found")
            raise HTTPException(
                status_code=401,
                detail="이메일 또는 비밀번호가 잘못되었습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 비밀번호 검증
        password_valid = verify_password(form_data.password, user["hashed_password"])
        print(f"🔑 Password valid: {password_valid}")

        if not password_valid:
            print("❌ Invalid password")
            raise HTTPException(
                status_code=401,
                detail="이메일 또는 비밀번호가 잘못되었습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 토큰 생성
        print("🎫 Creating access token...")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        print("✅ Login successful")
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        print(f"💥 Login error: {str(e)}")
        print(f"💥 Error type: {type(e)}")
        import traceback

        print(f"💥 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"로그인 실패: {str(e)}")


# 🔥 새로 추가된 /earnings 엔드포인트
@app.post("/earnings")
async def update_earnings(
    request: EarningsRequest, current_user: dict = Depends(get_current_user)
):
    """🔥 JWT에서 실제 사용자 ID 추출하여 수익 업데이트"""
    try:
        user_id = current_user["id"]  # 🚨 하드코딩 완전 제거!
        amount = request.amount

        print(f"💰 Updating earnings for user {user_id}: +{amount}")

        # 실제 사용자의 수익 업데이트
        await database.execute(
            "UPDATE users SET total_earnings = total_earnings + :amount WHERE id = :user_id",
            {"amount": amount, "user_id": user_id},
        )

        print(f"✅ Successfully updated earnings for user {user_id}")
        return {
            "success": True,
            "message": "수익이 업데이트되었습니다.",
            "user_id": user_id,
        }

    except Exception as e:
        print(f"❌ Earnings update error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """🔥 JWT에서 실제 사용자 ID 추출하여 개인화 대시보드 제공"""
    try:
        user_id = current_user["id"]  # 🚨 하드코딩 완전 제거!
        print(
            f"🎯 Dashboard request for REAL user ID: {user_id} (email: {current_user['email']})"
        )

        # 1. 실제 사용자별 수익 계산 (이번달, 지난달, 전체)
        earnings_query = """
        SELECT 
            -- 전체 수익
            COALESCE(SUM(primary_reward), 0) as primary_total,
            COALESCE(SUM(secondary_reward), 0) as secondary_total,
            COALESCE(SUM(primary_reward), 0) + COALESCE(SUM(secondary_reward), 0) as total,
            
            -- 이번달 수익
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE) 
                THEN primary_reward ELSE 0 END), 0) as this_month_primary,
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE) 
                THEN secondary_reward ELSE 0 END), 0) as this_month_secondary,
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE) 
                THEN primary_reward + COALESCE(secondary_reward, 0) ELSE 0 END), 0) as this_month_total,
            
            -- 지난달 수익
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') 
                THEN primary_reward ELSE 0 END), 0) as last_month_primary,
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') 
                THEN secondary_reward ELSE 0 END), 0) as last_month_secondary,
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') 
                THEN primary_reward + COALESCE(secondary_reward, 0) ELSE 0 END), 0) as last_month_total
        FROM transactions 
        WHERE user_id = :user_id
        """
        earnings_result = await database.fetch_one(earnings_query, {"user_id": user_id})

        # earnings_result가 None인 경우 기본값 설정
        if earnings_result is None:
            earnings_result = {
                "primary_total": 0,
                "secondary_total": 0,
                "total": 0,
                "this_month_primary": 0,
                "this_month_secondary": 0,
                "this_month_total": 0,
                "last_month_primary": 0,
                "last_month_secondary": 0,
                "last_month_total": 0,
            }

        # 월별 성장률 계산
        this_month_total = int(earnings_result["this_month_total"] or 0)
        last_month_total = int(earnings_result["last_month_total"] or 0)

        if last_month_total > 0:
            growth_rate = (
                (this_month_total - last_month_total) / last_month_total
            ) * 100
            growth_percentage = f"{growth_rate:+.1f}%"
            is_positive_growth = growth_rate >= 0
        else:
            growth_percentage = "N/A"
            is_positive_growth = True

        print(f"💰 User {user_id} earnings: {dict(earnings_result)}")
        print(
            f"📈 Growth: {growth_percentage} (this month: {this_month_total}, last month: {last_month_total})"
        )

        # 2. 사용자별 품질 이력 조회 (최근 4주간)
        quality_history = await database.fetch_all(
            """
            SELECT 
                week_label as name, 
                quality_score as score,
                recorded_at
            FROM user_quality_history 
            WHERE user_id = :user_id 
            ORDER BY recorded_at DESC LIMIT 4
            """,
            {"user_id": user_id},
        )

        # 품질 통계 계산
        if quality_history:
            scores = [row["score"] for row in quality_history]
            average_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)

            # 성장률 계산 (최신 vs 이전)
            if len(scores) >= 2:
                recent_score = scores[0]
                previous_score = scores[1]
                if previous_score > 0:
                    growth_rate = (
                        (recent_score - previous_score) / previous_score
                    ) * 100
                    growth_percentage = f"{growth_rate:+.1f}%"
                    is_positive_growth = growth_rate >= 0
                else:
                    growth_percentage = "N/A"
                    is_positive_growth = True
            else:
                growth_percentage = "N/A"
                is_positive_growth = True
        else:
            average_score = 75
            max_score = 75
            min_score = 75
            growth_percentage = "N/A"
            is_positive_growth = True

        # 3. 현재 사용자 품질 점수
        current_user_data = await database.fetch_one(
            "SELECT quality_score FROM users WHERE id = :user_id", {"user_id": user_id}
        )
        quality_score = current_user_data["quality_score"] if current_user_data else 75

        # 4. 일일 제출 현황 조회
        daily_submission = await database.fetch_one(
            """
            SELECT submission_count, quality_score_avg
            FROM daily_submissions 
            WHERE user_id = :user_id AND submission_date = CURRENT_DATE
            """,
            {"user_id": user_id},
        )

        # 일일 제출 현황이 없으면 기본값 설정
        if daily_submission is None:
            daily_submission = {
                "submission_count": 0,
                "quality_score_avg": quality_score,
            }

        # 5. 동적 제출 한도 계산
        submission_limit = calculate_dynamic_limit(quality_score)

        # 5. 사용자별 거래 내역 조회
        transactions = await database.fetch_all(
            """
            SELECT id, query_text as query, buyer_name as "buyerName", 
                   primary_reward as "primaryReward", secondary_reward as "secondaryReward",
                   status, created_at as timestamp
            FROM transactions 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            """,
            {"user_id": user_id},
        )
        print(f"📊 User {user_id} has {len(transactions)} transactions")

        # 6. 추가 통계 계산
        # 이번달 검색 횟수
        monthly_searches = await database.fetch_one(
            """
            SELECT COUNT(*) as count
            FROM search_queries 
            WHERE user_id = :user_id 
            AND created_at >= date_trunc('month', CURRENT_DATE)
            """,
            {"user_id": user_id},
        )
        monthly_search_count = (
            int(monthly_searches["count"] or 0) if monthly_searches else 0
        )

        # 경매 성공률
        auction_stats = await database.fetch_one(
            """
            SELECT 
                COUNT(*) as total_auctions,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_auctions
            FROM auctions 
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )

        if (
            auction_stats
            and auction_stats["total_auctions"]
            and auction_stats["total_auctions"] > 0
        ):
            success_rate = round(
                (auction_stats["completed_auctions"] / auction_stats["total_auctions"])
                * 100,
                1,
            )
        else:
            success_rate = 0.0

        # 평균 품질 점수
        avg_quality = await database.fetch_one(
            """
            SELECT AVG(quality_score) as avg_score
            FROM search_queries 
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        average_quality_score = (
            round(float(avg_quality["avg_score"] or 0), 1) if avg_quality else 0.0
        )

        print(
            f"📈 User {user_id} stats: searches={monthly_search_count}, success_rate={success_rate}%, avg_quality={average_quality_score}"
        )

        # 7. 응답 데이터 구성
        response_data = DashboardResponse(
            earnings={
                "total": int(earnings_result["total"] or 0),
                "primary": int(earnings_result["primary_total"] or 0),
                "secondary": int(earnings_result["secondary_total"] or 0),
                "thisMonth": {
                    "total": int(earnings_result["this_month_total"] or 0),
                    "primary": int(earnings_result["this_month_primary"] or 0),
                    "secondary": int(earnings_result["this_month_secondary"] or 0),
                },
                "lastMonth": {
                    "total": int(earnings_result["last_month_total"] or 0),
                    "primary": int(earnings_result["last_month_primary"] or 0),
                    "secondary": int(earnings_result["last_month_secondary"] or 0),
                },
                "growth": {
                    "percentage": growth_percentage,
                    "isPositive": is_positive_growth,
                },
            },
            qualityHistory=(
                [
                    QualityHistory(name=row["name"], score=row["score"])
                    for row in quality_history
                ]
                if quality_history
                else [
                    QualityHistory(name="Week 1", score=65),
                    QualityHistory(name="Week 2", score=70),
                    QualityHistory(name="Week 3", score=72),
                    QualityHistory(name="Week 4", score=quality_score),
                ]
            ),
            qualityStats={
                "average": round(average_score, 1),
                "max": max_score,
                "min": min_score,
                "growth": {
                    "percentage": growth_percentage,
                    "isPositive": is_positive_growth,
                },
                "recentScore": (
                    quality_history[0]["score"] if quality_history else quality_score
                ),
            },
            submissionLimit=submission_limit,
            dailySubmission={
                "count": int(daily_submission["submission_count"] or 0),
                "limit": submission_limit.dailyMax,
                "remaining": max(
                    0,
                    submission_limit.dailyMax
                    - int(daily_submission["submission_count"] or 0),
                ),
                "qualityScoreAvg": int(
                    daily_submission["quality_score_avg"] or quality_score
                ),
            },
            stats={
                "monthlySearches": monthly_search_count,
                "successRate": success_rate,
                "avgQualityScore": average_quality_score,
            },
            transactions=[
                {
                    "id": row["id"],
                    "query": row["query"],
                    "buyerName": row["buyerName"],
                    "primaryReward": int(row["primaryReward"]),
                    "secondaryReward": (
                        int(row["secondaryReward"]) if row["secondaryReward"] else None
                    ),
                    "status": row["status"],
                    "timestamp": (
                        row["timestamp"].isoformat()
                        if row["timestamp"]
                        else datetime.now().isoformat()
                    ),
                }
                for row in transactions
            ],
        )

        print(
            f"✅ Returning dashboard for user {user_id}: earnings={response_data.earnings}"
        )
        return response_data

    except Exception as e:
        print(f"❌ Dashboard error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@app.post("/quality-score")
async def update_quality_score(
    request: QualityScoreRequest, current_user: dict = Depends(get_current_user)
):
    """품질 점수 업데이트 및 이력 저장"""
    try:
        user_id = current_user["id"]
        score = request.score
        week_label = request.week_label

        print(f"📊 Updating quality score for user {user_id}: {score} ({week_label})")

        # 1. 현재 사용자의 품질 점수 업데이트
        await database.execute(
            "UPDATE users SET quality_score = :score WHERE id = :user_id",
            {"score": score, "user_id": user_id},
        )

        # 2. 품질 이력에 저장
        await database.execute(
            """
            INSERT INTO user_quality_history (user_id, week_label, quality_score, recorded_at)
            VALUES (:user_id, :week_label, :score, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, week_label) 
            DO UPDATE SET 
                quality_score = :score,
                recorded_at = CURRENT_TIMESTAMP
            """,
            {"user_id": user_id, "week_label": week_label, "score": score},
        )

        print(f"✅ Successfully updated quality score for user {user_id}")
        return {
            "success": True,
            "message": "품질 점수가 업데이트되었습니다.",
            "user_id": user_id,
            "score": score,
            "week_label": week_label,
        }

    except Exception as e:
        print(f"❌ Quality score update error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submission")
async def update_daily_submission(
    request: SubmissionRequest, current_user: dict = Depends(get_current_user)
):
    """일일 제출 현황 업데이트"""
    try:
        user_id = current_user["id"]
        quality_score = request.quality_score

        print(
            f"📝 Updating daily submission for user {user_id}: quality_score={quality_score}"
        )

        # 1. 일일 제출 현황 업데이트 (INSERT 또는 UPDATE)
        await database.execute(
            """
            INSERT INTO daily_submissions (user_id, submission_date, submission_count, quality_score_avg)
            VALUES (:user_id, CURRENT_DATE, 1, :quality_score)
            ON CONFLICT (user_id, submission_date) 
            DO UPDATE SET 
                submission_count = daily_submissions.submission_count + 1,
                quality_score_avg = (
                    (daily_submissions.quality_score_avg * daily_submissions.submission_count + :quality_score) 
                    / (daily_submissions.submission_count + 1)
                ),
                created_at = CURRENT_TIMESTAMP
            """,
            {"user_id": user_id, "quality_score": quality_score},
        )

        # 2. 사용자의 총 제출 수 업데이트
        await database.execute(
            "UPDATE users SET submission_count = submission_count + 1 WHERE id = :user_id",
            {"user_id": user_id},
        )

        print(f"✅ Successfully updated daily submission for user {user_id}")
        return {
            "success": True,
            "message": "제출 현황이 업데이트되었습니다.",
            "user_id": user_id,
            "quality_score": quality_score,
        }

    except Exception as e:
        print(f"❌ Daily submission update error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "user-service", "database": "connected"}
