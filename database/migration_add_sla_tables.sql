-- SLA 검증 지표를 저장하는 테이블 (Verification Service가 사용)
CREATE TABLE IF NOT EXISTS delivery_metrics (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(255) UNIQUE NOT NULL, -- 기존 transactions.bid_id와 연결될 ID
    v_atf FLOAT, -- Above The Fold 가시성
    l_fp FLOAT, -- 첫 가시성 지연 시간 (초)
    f_ratio FLOAT, -- 포커스 비율
    t_dwell FLOAT, -- 체류 시간 (초)
    x_ok BOOLEAN, -- 독점 충족 여부
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 최종 정산 결과를 저장하는 테이블 (Settlement Service가 사용)
CREATE TABLE IF NOT EXISTS settlements (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(255) UNIQUE NOT NULL,
    verification_decision VARCHAR(50) NOT NULL, -- 'PASSED', 'PARTIAL', 'FAILED'
    payable_amount NUMERIC(10, 2) NOT NULL, -- 사용자에게 최종 지급될 금액
    settled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

