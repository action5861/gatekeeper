-- 🗄️ 검색 데이터 거래 플랫폼 DB 스키마

-- 👥 사용자 테이블
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

-- 🏢 광고주 테이블
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

-- 🔍 검색 쿼리 테이블
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

-- 🏪 경매 테이블
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

-- 💰 입찰 테이블
CREATE TABLE IF NOT EXISTS bids (
    id VARCHAR(100) PRIMARY KEY,
    auction_id INTEGER REFERENCES auctions(id),
    buyer_name VARCHAR(100) NOT NULL,
    price INTEGER NOT NULL,
    bonus_description TEXT,
    landing_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 💸 거래 내역 테이블
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(100) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    auction_id INTEGER REFERENCES auctions(id),
    query_text VARCHAR(500) NOT NULL,
    buyer_name VARCHAR(100) NOT NULL,
    primary_reward DECIMAL(10,2) NOT NULL,
    secondary_reward DECIMAL(10,2),
    status VARCHAR(20) DEFAULT '1차 완료',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 📄 검증 요청 테이블
CREATE TABLE IF NOT EXISTS verification_requests (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) REFERENCES transactions(id),
    proof_file_path VARCHAR(500),
    verification_status VARCHAR(20) DEFAULT 'pending',
    verification_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- 📊 사용자 품질 이력 테이블
CREATE TABLE IF NOT EXISTS user_quality_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    quality_score INTEGER NOT NULL,
    week_label VARCHAR(20) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔍 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_advertisers_email ON advertisers(email);
CREATE INDEX IF NOT EXISTS idx_auctions_search_id ON auctions(search_id);
CREATE INDEX IF NOT EXISTS idx_auctions_status ON auctions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_verification_status ON verification_requests(verification_status);

-- 📝 샘플 데이터 삽입
INSERT INTO users (username, email, hashed_password, total_earnings, quality_score) VALUES 
('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kEa8E0zdy', 1500.00, 75),
('sampleuser', 'sample@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kEa8E0zdy', 850.00, 68)
ON CONFLICT (email) DO NOTHING;

INSERT INTO advertisers (username, email, hashed_password, company_name, daily_budget) VALUES 
('advertiser1', 'advertiser@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kEa8E0zdy', '광고회사', 50000.00),
('marketing_co', 'marketing@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kEa8E0zdy', '마케팅컴퍼니', 30000.00)
ON CONFLICT (email) DO NOTHING;

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

COMMIT; 