from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, Optional
import random
import asyncio
import httpx
from database import (
    database,
    connect_to_database,
    disconnect_from_database,
)
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.sign import verify_sig

app = FastAPI(title="Verification Service", version="1.0.0")


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


# Pydantic 모델
class VerifyRequest(BaseModel):
    searchId: str
    proof: str


class VerifyResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str


class ClaimRequest(BaseModel):
    transactionId: str
    proofFile: str


class ClaimResponse(BaseModel):
    status: str
    secondaryReward: Optional[int] = None


class VerifyClickRequest(BaseModel):
    bidId: str
    sig: str


class VerifyClickResponse(BaseModel):
    userId: int
    type: str
    payout: int
    destination: str


class DeliveryMetricsPayload(BaseModel):
    trade_id: str
    v_atf: float = 0.0  # 부정 방지용
    clicked: bool = False  # 광고 클릭 여부 (핵심!)
    t_dwell_on_ad_site: float = 0.0  # 광고주 사이트 체류 시간 (가장 중요!)
    # 아래는 deprecated (하위 호환용)
    l_fp: float = 0.0
    f_ratio: float = 0.0
    t_dwell: float = 0.0
    x_ok: bool = False
    t_dwell_before_click: float = 0.0


# OCR 및 외부 API 연동을 통한 검증 과정을 시뮬레이션
async def simulate_verification() -> dict:
    """검증 과정을 시뮬레이션합니다."""
    await asyncio.sleep(2)  # 2초의 처리 시간 흉내
    is_success = random.random() > 0.3  # 70% 성공 확률
    return {
        "success": is_success,
        "reward": (
            random.randint(500, 1000) if is_success else 0
        ),  # 500-1000원 사이의 2차 보상
    }


@app.post("/verify", response_model=VerifyResponse)
async def verify_proof(request: VerifyRequest):
    """2차 보상을 위한 활동 증빙 제출 및 처리"""
    try:
        # 입력값 유효성 검사
        if not request.searchId:
            raise HTTPException(status_code=400, detail="유효하지 않은 검색 ID입니다.")

        if not request.proof:
            raise HTTPException(status_code=400, detail="증빙 자료를 제출해주세요.")

        # (시뮬레이션) 처리 지연
        await asyncio.sleep(2)

        # (시뮬레이션) 70% 확률로 검증 성공, 30% 확률로 검증 실패
        is_verification_success = random.random() < 0.7

        # 검증 요청을 DB에 저장
        verification_query = """
            INSERT INTO verification_requests (transaction_id, proof_file_path, verification_status, verification_result)
            VALUES (:transaction_id, :proof_file_path, :verification_status, :verification_result)
        """

        verification_result = {
            "searchId": request.searchId,
            "verificationStatus": "success" if is_verification_success else "failed",
            "reason": (
                "제출된 증빙 자료가 기준에 미달합니다."
                if not is_verification_success
                else None
            ),
        }

        await database.execute(
            verification_query,
            {
                "transaction_id": request.searchId,
                "proof_file_path": request.proof,
                "verification_status": "completed",
                "verification_result": verification_result,
            },
        )

        if is_verification_success:
            # 검증 성공: 2차 보상 지급
            secondary_reward_amount = random.randint(500, 3500)  # 500~3500원 랜덤

            # 거래 내역 업데이트 (2차 보상 추가)
            update_transaction_query = """
                UPDATE transactions 
                SET secondary_reward = :secondary_reward, status = '2차 완료'
                WHERE id = :transaction_id
            """

            await database.execute(
                update_transaction_query,
                {
                    "secondary_reward": secondary_reward_amount,
                    "transaction_id": request.searchId,
                },
            )

            return VerifyResponse(
                success=True,
                data={
                    "searchId": request.searchId,
                    "secondaryRewardAmount": secondary_reward_amount,
                    "verificationStatus": "success",
                },
                message="검증 성공: 2차 보상이 지급되었습니다.",
            )

        else:
            # 검증 실패 시 거래 상태 업데이트
            update_transaction_query = """
                UPDATE transactions 
                SET status = '검증 실패'
                WHERE id = :transaction_id
            """

            await database.execute(
                update_transaction_query,
                {
                    "transaction_id": request.searchId,
                },
            )

            return VerifyResponse(
                success=False,
                data={
                    "searchId": request.searchId,
                    "verificationStatus": "failed",
                    "reason": "제출된 증빙 자료가 기준에 미달합니다.",
                },
                message="검증 실패",
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.post("/claim", response_model=ClaimResponse)
async def claim_reward(transactionId: str = Form(...), proof: UploadFile = File(...)):
    """2차 보상 청구를 처리합니다."""
    try:
        if not transactionId or not proof:
            raise HTTPException(status_code=400, detail="잘못된 요청입니다.")

        print(f"2차 보상 요청 접수: {transactionId}, 증빙 파일: {proof.filename}")

        # 2차 보상 청구를 DB에 저장
        claim_query = """
            INSERT INTO verification_requests (transaction_id, proof_file_path, verification_status)
            VALUES (:transaction_id, :proof_file_path, :verification_status)
        """

        await database.execute(
            claim_query,
            {
                "transaction_id": transactionId,
                "proof_file_path": proof.filename,
                "verification_status": "pending",
            },
        )

        verification_result = await simulate_verification()

        if verification_result["success"]:
            # 거래 내역 업데이트 (2차 보상 추가)
            update_transaction_query = """
                UPDATE transactions 
                SET secondary_reward = :secondary_reward, status = '2차 완료'
                WHERE id = :transaction_id
            """

            await database.execute(
                update_transaction_query,
                {
                    "secondary_reward": verification_result["reward"],
                    "transaction_id": transactionId,
                },
            )

            return ClaimResponse(
                status="2차 완료", secondaryReward=verification_result["reward"]
            )
        else:
            # 검증 실패 시 거래 상태 업데이트
            update_transaction_query = """
                UPDATE transactions 
                SET status = '검증 실패'
                WHERE id = :transaction_id
            """

            await database.execute(
                update_transaction_query,
                {
                    "transaction_id": transactionId,
                },
            )

            return ClaimResponse(status="검증 실패")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.post("/verify-click", response_model=VerifyClickResponse)
async def verify_click(request: VerifyClickRequest):
    """클릭 검증 및 컨텍스트 반환"""
    try:
        # 1. DB에서 입찰 정보 조회
        bid_query = """
            SELECT id, user_id, type, price, dest_url, landing_url
            FROM bids 
            WHERE id = :bid_id
        """
        bid = await database.fetch_one(bid_query, {"bid_id": request.bidId})

        if not bid:
            raise HTTPException(status_code=400, detail="Unknown bid")

        # 2. 타입과 지급액 결정
        bid_type = "PLATFORM" if bid["type"] == "PLATFORM" else "ADVERTISER"
        payout = 200 if bid_type == "PLATFORM" else int(bid["price"])

        # 3. 서명 검증
        if not verify_sig(bid["id"], payout, bid_type, request.sig):
            raise HTTPException(status_code=400, detail="Bad signature")

        # 4. 응답 반환
        return VerifyClickResponse(
            userId=bid["user_id"],
            type=bid_type,
            payout=payout,
            destination=bid["dest_url"] or bid["landing_url"],
        )

    except Exception as e:
        print(f"❌ Click verification error: {e}")
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")


@app.post("/verify-delivery")
async def verify_delivery_and_trigger_settlement(payload: DeliveryMetricsPayload):
    """
    SLA 지표를 받아 검증하고 Settlement Service로 전달합니다.
    - delivery_metrics 테이블에 SLA 지표 저장
    - SLA 판정 로직 실행
    - Settlement Service에 판정 결과 전달
    """
    try:
        print(f"📊 Verifying delivery metrics for trade_id: {payload.trade_id}")

        # 1. 수신된 SLA 지표를 delivery_metrics 테이블에 저장 (중복 시 무시)
        await database.execute(
            """INSERT INTO delivery_metrics (trade_id, v_atf, clicked, t_dwell_on_ad_site)
               VALUES (:trade_id, :v_atf, :clicked, :t_dwell_on_ad_site)
               ON CONFLICT (trade_id) DO UPDATE
               SET v_atf = EXCLUDED.v_atf, 
                   clicked = EXCLUDED.clicked,
                   t_dwell_on_ad_site = GREATEST(delivery_metrics.t_dwell_on_ad_site, EXCLUDED.t_dwell_on_ad_site)""",
            values={
                "trade_id": payload.trade_id,
                "v_atf": payload.v_atf,
                "clicked": payload.clicked,
                "t_dwell_on_ad_site": payload.t_dwell_on_ad_site,
            },
        )
        print(f"✅ Saved delivery metrics for trade_id: {payload.trade_id}")

        # 2. 🎯 단순하고 합리적인 SLA 판정 로직
        decision = "FAILED"

        print(f"📊 Evaluating SLA for trade_id: {payload.trade_id}")
        print(f"   - Clicked: {payload.clicked}")
        print(f"   - v_atf: {payload.v_atf} (부정 방지용)")
        print(f"   - t_dwell_on_ad_site: {payload.t_dwell_on_ad_site}s (핵심!)")

        # 클릭 안함 = 무조건 FAILED
        if not payload.clicked:
            decision = "FAILED"
            print(f"❌ SLA FAILED for trade_id: {payload.trade_id}")
            print(f"   광고 클릭 안함")
        # 화면에 안 보이는데 클릭 = 부정 의심 (봇)
        elif payload.v_atf < 0.3:
            decision = "FAILED"
            print(f"❌ SLA FAILED for trade_id: {payload.trade_id}")
            print(f"   부정 클릭 의심 (v_atf: {payload.v_atf} < 0.3)")
        # 광고주 사이트 체류 시간으로 평가 (선형 보상 시스템)
        elif payload.t_dwell_on_ad_site >= 20.0:
            decision = "PASSED"
            print(f"✅ SLA PASSED for trade_id: {payload.trade_id}")
            print(
                f"   광고 클릭 + 광고주 사이트 20초 이상 체류 ({payload.t_dwell_on_ad_site:.2f}s)"
            )
        elif payload.t_dwell_on_ad_site > 3.0:
            decision = "PARTIAL"
            print(f"⚠️ SLA PARTIAL for trade_id: {payload.trade_id}")
            print(
                f"   광고 클릭 + 광고주 사이트 3초 초과 체류 ({payload.t_dwell_on_ad_site:.2f}s, 3s < dwell < 20s)"
            )
        else:
            # 클릭했지만 광고주 사이트 체류 시간이 3초 이하 = FAILED
            decision = "FAILED"
            print(f"❌ SLA FAILED for trade_id: {payload.trade_id}")
            print(
                f"   광고 클릭 O, 하지만 체류 시간 부족 ({payload.t_dwell_on_ad_site:.2f}s <= 3s)"
            )

        # 3. Settlement Service에 판정 결과 전달
        settlement_service_url = os.getenv(
            "SETTLEMENT_SERVICE_URL", "http://settlement-service:8003"
        )
        settlement_endpoint = f"{settlement_service_url}/settle-trade"

        print(f"📤 Sending settlement request to: {settlement_endpoint}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settlement_endpoint,
                json={
                    "trade_id": payload.trade_id,
                    "verification_decision": decision,
                    "dwell_time": payload.t_dwell_on_ad_site,  # 직접 전달
                    "metrics": payload.dict(),
                },
            )

            if response.status_code == 200:
                print(
                    f"✅ Settlement request successful for trade_id: {payload.trade_id}"
                )
            else:
                print(f"⚠️ Settlement request returned status {response.status_code}")

        return {
            "status": "processing",
            "decision": decision,
            "trade_id": payload.trade_id,
            "message": f"SLA 검증 완료. 판정: {decision}",
        }

    except Exception as e:
        print(f"❌ Error in verify_delivery: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"SLA 검증 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/update-pending-return")
async def update_pending_return(request: dict):
    """1차 평가: 광고 클릭 시 PENDING_RETURN 상태로 업데이트"""
    try:
        trade_id = request.get("trade_id")
        if not trade_id:
            raise HTTPException(status_code=400, detail="trade_id is required")

        print(
            f"📝 [1st Evaluation] Updating to PENDING_RETURN for trade_id: {trade_id}"
        )

        # transactions 테이블의 상태를 PENDING_RETURN으로 업데이트
        await database.execute(
            """UPDATE transactions
               SET status = 'PENDING_RETURN'
               WHERE id = :trade_id""",
            values={"trade_id": trade_id},
        )

        print(
            f"✅ [1st Evaluation] Status updated to PENDING_RETURN for trade_id: {trade_id}"
        )

        return {
            "status": "ok",
            "decision": "PENDING_RETURN",
            "message": "사용자 복귀 대기 중",
        }
    except Exception as e:
        print(f"❌ Error in update_pending_return: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify-return")
async def verify_return(request: dict):
    """2차 평가: 사용자 복귀 시 체류 시간 기반 최종 평가"""
    try:
        trade_id = request.get("trade_id")
        dwell_time = request.get("dwell_time", 0)

        if not trade_id:
            raise HTTPException(status_code=400, detail="trade_id is required")

        print(f"🔙 [2nd Evaluation] User returned for trade_id: {trade_id}")
        print(f"   Dwell time: {dwell_time:.2f}s")

        # delivery_metrics 테이블에 체류 시간 저장
        await database.execute(
            """UPDATE delivery_metrics
               SET t_dwell_on_ad_site = :dwell_time
               WHERE trade_id = :trade_id""",
            values={"trade_id": trade_id, "dwell_time": dwell_time},
        )

        # SLA 기준에 따라 판정 (선형 보상 시스템)
        decision = "FAILED"

        if dwell_time >= 20.0:
            decision = "PASSED"
            print(f"✅ [2nd Evaluation] PASSED - Dwell time >= 20s")
        elif dwell_time > 3.0:
            decision = "PARTIAL"
            print(
                f"⚠️ [2nd Evaluation] PARTIAL - Dwell time: {dwell_time:.2f}s (3s < dwell < 20s)"
            )
        else:
            decision = "FAILED"  # 3초 이하는 보상 없음
            print(
                f"❌ [2nd Evaluation] FAILED - Dwell time too short: {dwell_time:.2f}s (<= 3s)"
            )

        # transactions 테이블 상태 업데이트
        await database.execute(
            """UPDATE transactions
               SET status = :status
               WHERE id = :trade_id""",
            values={"trade_id": trade_id, "status": decision},
        )

        # Settlement Service에 판정 결과 전달
        settlement_service_url = os.getenv(
            "SETTLEMENT_SERVICE_URL", "http://settlement-service:8003"
        )
        settlement_endpoint = f"{settlement_service_url}/settle-trade"

        print(f"📤 Sending settlement request to: {settlement_endpoint}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settlement_endpoint,
                json={
                    "trade_id": trade_id,
                    "verification_decision": decision,
                    "dwell_time": dwell_time,
                    "metrics": {
                        "t_dwell": dwell_time,
                        "t_dwell_on_ad_site": dwell_time,
                        "dwell_time": dwell_time,  # 추가 필드명
                    },
                },
            )

            if response.status_code == 200:
                print(f"✅ Settlement request successful for trade_id: {trade_id}")
            else:
                print(f"⚠️ Settlement request returned status {response.status_code}")

        return {
            "status": "completed",
            "decision": decision,
            "trade_id": trade_id,
            "dwell_time": dwell_time,
            "message": f"2차 평가 완료. 판정: {decision}",
        }

    except Exception as e:
        print(f"❌ Error in verify_return: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "verification-service",
        "database": "connected",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
