from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, Optional
import random
import asyncio
from database import (
    database,
    connect_to_database,
    disconnect_from_database,
)

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
