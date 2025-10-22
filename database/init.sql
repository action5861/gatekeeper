-- 검색 데이터 거래 플랫폼 DB 스키마

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_earnings DECIMAL(10,2) DEFAULT 0.00,
    quality_score INTEGER DEFAULT 50,
    submission_count INTEGER DEFAULT 0
);

-- 광고주 테이블
CREATE TABLE IF NOT EXISTS advertisers (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    company_name VARCHAR(100) NOT NULL,
    website_url VARCHAR(255),
    daily_budget DECIMAL(10,2) DEFAULT 10000.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 검색 쿼리 테이블
CREATE TABLE IF NOT EXISTS search_queries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query_text VARCHAR(500) NOT NULL,
    quality_score INTEGER NOT NULL,
    commercial_value VARCHAR(20) NOT NULL,
    keywords JSONB,
    suggestions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 경매 테이블
CREATE TABLE IF NOT EXISTS auctions (
    id SERIAL PRIMARY KEY,
    search_id VARCHAR(100) UNIQUE NOT NULL,
    query_text VARCHAR(500) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    selected_bid_id VARCHAR(100)
);

-- 입찰 테이블
CREATE TABLE IF NOT EXISTS bids (
    id VARCHAR(100) PRIMARY KEY,
    auction_id INTEGER REFERENCES auctions(id),
    buyer_name VARCHAR(100) NOT NULL,
    price INTEGER NOT NULL,
    bonus_description TEXT,
    landing_url TEXT,
    type VARCHAR(20) DEFAULT 'ADVERTISER' CHECK (type IN ('ADVERTISER', 'PLATFORM')),
    user_id INTEGER REFERENCES users(id),
    dest_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 거래 내역 테이블
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(100) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    auction_id INTEGER REFERENCES auctions(id),
    bid_id VARCHAR(100),
    advertiser_id INTEGER REFERENCES advertisers(id),
    query_text VARCHAR(500) NOT NULL,
    buyer_name VARCHAR(100) NOT NULL,
    primary_reward DECIMAL(10,2) NOT NULL,
    secondary_reward DECIMAL(10,2),
    amount DECIMAL(10,2),
    source VARCHAR(20) DEFAULT 'ADVERTISER' CHECK (source IN ('ADVERTISER', 'PLATFORM')),
    reason VARCHAR(100),
    status VARCHAR(20) DEFAULT '1차 완료',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 검증 요청 테이블
CREATE TABLE IF NOT EXISTS verification_requests (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) REFERENCES transactions(id),
    proof_file_path VARCHAR(500),
    verification_status VARCHAR(20) DEFAULT 'pending',
    verification_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- 사용자 품질 이력 테이블 (UNIQUE 제약조건 추가)
CREATE TABLE IF NOT EXISTS user_quality_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    quality_score INTEGER NOT NULL,
    week_label VARCHAR(20) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, week_label)
);

-- 일일 제출 현황 테이블
CREATE TABLE IF NOT EXISTS daily_submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    submission_date DATE DEFAULT CURRENT_DATE,
    submission_count INTEGER DEFAULT 0,
    quality_score_avg INTEGER DEFAULT 0,
    total_quality_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, submission_date)
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_advertisers_email ON advertisers(email);
CREATE INDEX IF NOT EXISTS idx_auctions_search_id ON auctions(search_id);
CREATE INDEX IF NOT EXISTS idx_auctions_status ON auctions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_bid ON transactions(bid_id);
CREATE INDEX IF NOT EXISTS idx_bids_user ON bids(user_id);
CREATE INDEX IF NOT EXISTS idx_verification_status ON verification_requests(verification_status);
CREATE INDEX IF NOT EXISTS idx_daily_submissions_user_date ON daily_submissions(user_id, submission_date);

-- 샘플 데이터 삽입
INSERT INTO users (username, email, hashed_password, total_earnings, quality_score) VALUES 
('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kEa8E0zdy', 1500.00, 75),
('sampleuser', 'sample@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kEa8E0zdy', 850.00, 68)
ON CONFLICT (email) DO NOTHING;

INSERT INTO advertisers (username, email, hashed_password, company_name, daily_budget) VALUES 
('advertiser1', 'advertiser@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kEa8E0zdy', '광고회사', 50000.00),
('marketing_co', 'marketing@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kEa8E0zdy', '마케팅컴퍼니', 30000.00)
ON CONFLICT (email) DO NOTHING;

-- 샘플 검색 쿼리
INSERT INTO search_queries (user_id, query_text, quality_score, commercial_value, created_at) VALUES 
(1, '아이폰16 프로', 85, 'high', '2025-01-15T10:30:00Z'),
(1, '삼성 갤럭시 S24', 78, 'high', '2025-01-16T14:20:00Z'),
(1, '제주도 호텔 예약', 92, 'medium', '2025-01-17T09:15:00Z'),
(1, '나이키 운동화 추천', 75, 'high', '2025-01-18T16:45:00Z'),
(1, '맥북 프로 16인치', 88, 'high', '2025-01-19T11:30:00Z'),
(2, '아디다스 운동화', 72, 'medium', '2025-01-15T13:20:00Z'),
(2, '부산 여행 가이드', 68, 'low', '2025-01-16T15:10:00Z'),
(2, 'LG OLED TV', 81, 'high', '2025-01-17T10:45:00Z')
ON CONFLICT DO NOTHING;

-- 샘플 경매 데이터
INSERT INTO auctions (search_id, query_text, user_id, status, created_at, expires_at) VALUES 
('search_001', '아이폰16 프로', 1, 'completed', '2025-01-15T10:30:00Z', '2025-01-22T10:30:00Z'),
('search_002', '삼성 갤럭시 S24', 1, 'completed', '2025-01-16T14:20:00Z', '2025-01-23T14:20:00Z'),
('search_003', '제주도 호텔 예약', 1, 'active', '2025-01-17T09:15:00Z', '2025-01-24T09:15:00Z'),
('search_004', '나이키 운동화 추천', 1, 'completed', '2025-01-18T16:45:00Z', '2025-01-25T16:45:00Z'),
('search_005', '맥북 프로 16인치', 1, 'active', '2025-01-19T11:30:00Z', '2025-01-26T11:30:00Z'),
('search_006', '아디다스 운동화', 2, 'completed', '2025-01-15T13:20:00Z', '2025-01-22T13:20:00Z'),
('search_007', '부산 여행 가이드', 2, 'expired', '2025-01-16T15:10:00Z', '2025-01-23T15:10:00Z'),
('search_008', 'LG OLED TV', 2, 'active', '2025-01-17T10:45:00Z', '2025-01-24T10:45:00Z')
ON CONFLICT (search_id) DO NOTHING;

-- 샘플 거래 내역
INSERT INTO transactions (id, user_id, query_text, buyer_name, primary_reward, secondary_reward, status, created_at) VALUES 
('txn_1001', 1, '아이폰16', '쿠팡', 175.00, NULL, '1차 완료', '2025-07-20T09:10:00Z'),
('txn_1002', 1, '제주도 항공권', '네이버', 250.00, 1250.00, '2차 완료', '2025-07-19T14:30:00Z'),
('txn_1003', 2, '나이키 운동화', 'Google', 90.00, NULL, '검증 실패', '2025-07-18T18:00:00Z')
ON CONFLICT (id) DO NOTHING;

-- 품질 이력 샘플 데이터
INSERT INTO user_quality_history (user_id, quality_score, week_label) VALUES 
(1, 65, 'Week 1'),
(1, 70, 'Week 2'),
(1, 72, 'Week 3'),
(1, 75, 'Week 4'),
(2, 60, 'Week 1'),
(2, 65, 'Week 2'),
(2, 67, 'Week 3'),
(2, 68, 'Week 4');

-- 일일 제출 현황 샘플 데이터
INSERT INTO daily_submissions (user_id, submission_date, submission_count, quality_score_avg) VALUES 
(1, CURRENT_DATE, 8, 75),
(1, CURRENT_DATE - INTERVAL '1 day', 12, 72),
(1, CURRENT_DATE - INTERVAL '2 day', 15, 70),
(2, CURRENT_DATE, 5, 68),
(2, CURRENT_DATE - INTERVAL '1 day', 7, 65)
ON CONFLICT (user_id, submission_date) DO NOTHING;

-- 광고주 키워드 테이블
CREATE TABLE IF NOT EXISTS advertiser_keywords (
    id SERIAL PRIMARY KEY,
    advertiser_id INTEGER REFERENCES advertisers(id) ON DELETE CASCADE,
    keyword VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    match_type VARCHAR(20) DEFAULT 'broad' CHECK (match_type IN ('exact', 'phrase', 'broad')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 광고주 카테고리 테이블  
CREATE TABLE IF NOT EXISTS advertiser_categories (
    id SERIAL PRIMARY KEY,
    advertiser_id INTEGER REFERENCES advertisers(id) ON DELETE CASCADE,
    category_path VARCHAR(200) NOT NULL,
    category_level INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 비즈니스 카테고리 마스터 테이블
CREATE TABLE IF NOT EXISTS business_categories (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES business_categories(id),
    name VARCHAR(100) NOT NULL,
    path VARCHAR(200) NOT NULL,
    level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 3),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 광고주 심사 상태 테이블
CREATE TABLE IF NOT EXISTS advertiser_reviews (
    id SERIAL PRIMARY KEY,
    advertiser_id INTEGER REFERENCES advertisers(id) ON DELETE CASCADE,
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'in_progress', 'approved', 'rejected')),
    reviewer_id INTEGER,
    review_notes TEXT,
    website_analysis TEXT,
    recommended_bid_min INTEGER DEFAULT 100,
    recommended_bid_max INTEGER DEFAULT 5000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 자동 입찰 설정 테이블
CREATE TABLE IF NOT EXISTS auto_bid_settings (
    id SERIAL PRIMARY KEY,
    advertiser_id INTEGER REFERENCES advertisers(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT false,
    daily_budget DECIMAL(10,2) DEFAULT 10000.00,
    max_bid_per_keyword INTEGER DEFAULT 3000,
    min_quality_score INTEGER DEFAULT 50,
    preferred_categories JSONB,
    excluded_keywords TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 추가 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_advertiser_keywords_keyword ON advertiser_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_advertiser_categories_path ON advertiser_categories(category_path);
CREATE INDEX IF NOT EXISTS idx_business_categories_parent ON business_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_advertiser_reviews_status ON advertiser_reviews(review_status);
CREATE INDEX IF NOT EXISTS idx_auto_bid_settings_enabled ON auto_bid_settings(is_enabled);

-- 자동 입찰 로그 테이블 (머신러닝 분석용)
CREATE TABLE IF NOT EXISTS auto_bid_logs (
    id SERIAL PRIMARY KEY,
    advertiser_id INTEGER REFERENCES advertisers(id) ON DELETE CASCADE,
    search_query VARCHAR(500) NOT NULL,
    match_type VARCHAR(20) NOT NULL,
    match_score DECIMAL(3,2) NOT NULL,
    bid_amount INTEGER NOT NULL,
    bid_result VARCHAR(20) NOT NULL CHECK (bid_result IN ('won', 'lost', 'timeout')),
    quality_score INTEGER,
    competitor_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 자동 입찰 로그 인덱스
CREATE INDEX IF NOT EXISTS idx_auto_bid_logs_advertiser ON auto_bid_logs(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_auto_bid_logs_created_at ON auto_bid_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_auto_bid_logs_result ON auto_bid_logs(bid_result);
CREATE INDEX IF NOT EXISTS idx_auto_bid_logs_match_type ON auto_bid_logs(match_type);

-- 비즈니스 카테고리 샘플 데이터

-- 대분류 (Level 1)
INSERT INTO business_categories (name, path, level, sort_order) VALUES
('전자제품', '전자제품', 1, 1),
('패션/뷰티', '패션/뷰티', 1, 2),
('생활/건강', '생활/건강', 1, 3),
('식품/음료', '식품/음료', 1, 4),
('스포츠/레저/자동차', '스포츠/레저/자동차', 1, 5),
('유아/아동', '유아/아동', 1, 6),
('여행/문화', '여행/문화', 1, 7),
('반려동물', '반려동물', 1, 8),
('디지털 콘텐츠', '디지털 콘텐츠', 1, 9),
('부동산/인테리어', '부동산/인테리어', 1, 10),
('의료/건강', '의료/건강', 1, 11),
('서비스', '서비스', 1, 12),
('교육/도서', '교육/도서', 1, 13)
ON CONFLICT DO NOTHING;

-- 중분류 (Level 2) 및 소분류 (Level 3)

-- 1. 전자제품
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(1, '스마트폰/태블릿', '전자제품 > 스마트폰/태블릿', 2, 1),
(1, '컴퓨터/노트북', '전자제품 > 컴퓨터/노트북', 2, 2),
(1, '가전제품', '전자제품 > 가전제품', 2, 3),
(1, '게임/콘솔', '전자제품 > 게임/콘솔', 2, 4),
(1, '카메라/캠코더', '전자제품 > 카메라/캠코더', 2, 5),
(1, '음향기기', '전자제품 > 음향기기', 2, 6)
ON CONFLICT DO NOTHING;

-- 2. 패션/뷰티
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(2, '여성의류', '패션/뷰티 > 여성의류', 2, 1),
(2, '남성의류', '패션/뷰티 > 남성의류', 2, 2),
(2, '패션잡화', '패션/뷰티 > 패션잡화', 2, 3),
(2, '뷰티/화장품', '패션/뷰티 > 뷰티/화장품', 2, 4),
(2, '주얼리/시계', '패션/뷰티 > 주얼리/시계', 2, 5)
ON CONFLICT DO NOTHING;

-- 3. 생활/건강
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(3, '가구/인테리어', '생활/건강 > 가구/인테리어', 2, 1),
(3, '주방용품', '생활/건강 > 주방용품', 2, 2),
(3, '생활용품', '생활/건강 > 생활용품', 2, 3),
(3, '건강/의료용품', '생활/건강 > 건강/의료용품', 2, 4)
ON CONFLICT DO NOTHING;

-- 4. 식품/음료
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(4, '신선식품', '식품/음료 > 신선식품', 2, 1),
(4, '가공식품', '식품/음료 > 가공식품', 2, 2),
(4, '건강식품', '식품/음료 > 건강식품', 2, 3),
(4, '음료/주류', '식품/음료 > 음료/주류', 2, 4)
ON CONFLICT DO NOTHING;

-- 5. 스포츠/레저/자동차
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(5, '스포츠의류/용품', '스포츠/레저/자동차 > 스포츠의류/용품', 2, 1),
(5, '캠핑/낚시', '스포츠/레저/자동차 > 캠핑/낚시', 2, 2),
(5, '자동차용품', '스포츠/레저/자동차 > 자동차용품', 2, 3),
(5, '자전거/킥보드', '스포츠/레저/자동차 > 자전거/킥보드', 2, 4)
ON CONFLICT DO NOTHING;

-- 6. 유아/아동
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(6, '출산/유아용품', '유아/아동 > 출산/유아용품', 2, 1),
(6, '장난감/완구', '유아/아동 > 장난감/완구', 2, 2),
(6, '유아동 의류/잡화', '유아/아동 > 유아동 의류/잡화', 2, 3)
ON CONFLICT DO NOTHING;

-- 7. 여행/문화
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(7, '국내여행', '여행/문화 > 국내여행', 2, 1),
(7, '해외여행', '여행/문화 > 해외여행', 2, 2),
(7, '항공권/숙박', '여행/문화 > 항공권/숙박', 2, 3),
(7, '티켓/공연', '여행/문화 > 티켓/공연', 2, 4)
ON CONFLICT DO NOTHING;

-- 8. 반려동물
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(8, '강아지용품', '반려동물 > 강아지용품', 2, 1),
(8, '고양이용품', '반려동물 > 고양이용품', 2, 2),
(8, '기타 반려동물용품', '반려동물 > 기타 반려동물용품', 2, 3)
ON CONFLICT DO NOTHING;

-- 9. 디지털 콘텐츠
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(9, '온라인 강의', '디지털 콘텐츠 > 온라인 강의', 2, 1),
(9, '소프트웨어', '디지털 콘텐츠 > 소프트웨어', 2, 2),
(9, '구독 서비스', '디지털 콘텐츠 > 구독 서비스', 2, 3)
ON CONFLICT DO NOTHING;

-- 10. 부동산/인테리어
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(10, '아파트/주택', '부동산/인테리어 > 아파트/주택', 2, 1),
(10, '상가/사무실', '부동산/인테리어 > 상가/사무실', 2, 2),
(10, '인테리어 시공', '부동산/인테리어 > 인테리어 시공', 2, 3)
ON CONFLICT DO NOTHING;

-- 11. 의료/건강
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(11, '병원/의원', '의료/건강 > 병원/의원', 2, 1),
(11, '약국', '의료/건강 > 약국', 2, 2),
(11, '건강검진', '의료/건강 > 건강검진', 2, 3)
ON CONFLICT DO NOTHING;

-- 12. 서비스
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(12, '금융/보험', '서비스 > 금융/보험', 2, 1),
(12, '법률/세무', '서비스 > 법률/세무', 2, 2),
(12, '마케팅/컨설팅', '서비스 > 마케팅/컨설팅', 2, 3),
(12, '운송/배달', '서비스 > 운송/배달', 2, 4)
ON CONFLICT DO NOTHING;

-- 13. 교육/도서
INSERT INTO business_categories (parent_id, name, path, level, sort_order) VALUES
-- 중분류
(13, '초/중/고 교육', '교육/도서 > 초/중/고 교육', 2, 1),
(13, '대학교육/성인학습', '교육/도서 > 대학교육/성인학습', 2, 2),
(13, '온라인강의/자격증', '교육/도서 > 온라인강의/자격증', 2, 3),
(13, '도서/음반', '교육/도서 > 도서/음반', 2, 4)
ON CONFLICT DO NOTHING;

COMMIT; 