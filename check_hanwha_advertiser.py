#!/usr/bin/env python3
"""
한화생명 광고주 카테고리 및 매칭 설정 확인 스크립트
"""
import asyncio
import os
from databases import Database

# 데이터베이스 연결 정보
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:your_secure_password_123@localhost:5433/search_exchange_db",
)

database = Database(DATABASE_URL)


async def check_hanwha_advertiser():
    """한화생명 광고주 정보 확인"""
    await database.connect()
    
    try:
        print("=" * 80)
        print("한화생명 광고주 정보 확인")
        print("=" * 80)
        
        # 1. 광고주 기본 정보
        print("\n[1] 광고주 기본 정보")
        print("-" * 80)
        advertiser = await database.fetch_one(
            """
            SELECT 
                id,
                company_name,
                website_url,
                category,
                approval_status,
                created_at
            FROM advertisers
            WHERE company_name LIKE '%한화생명%' OR company_name LIKE '%한화%'
            """
        )
        
        if not advertiser:
            print("❌ 한화생명 광고주를 찾을 수 없습니다.")
            return
        
        print(f"ID: {advertiser['id']}")
        print(f"회사명: {advertiser['company_name']}")
        print(f"웹사이트: {advertiser['website_url']}")
        print(f"표준 카테고리: {advertiser['category'] or '❌ 미설정'}")
        print(f"승인 상태: {advertiser['approval_status']}")
        print(f"생성일: {advertiser['created_at']}")
        
        advertiser_id = advertiser['id']
        
        # 2. advertiser_categories 테이블 확인
        print("\n[2] 비즈니스 카테고리 설정 (advertiser_categories)")
        print("-" * 80)
        categories = await database.fetch_all(
            """
            SELECT 
                id,
                category_path,
                category_level,
                is_primary,
                source
            FROM advertiser_categories
            WHERE advertiser_id = :advertiser_id
            """
            , {"advertiser_id": advertiser_id}
        )
        
        if not categories:
            print("❌ 카테고리가 설정되지 않았습니다.")
        else:
            for cat in categories:
                print(f"  - 경로: {cat['category_path']}")
                print(f"    레벨: {cat['category_level']}")
                print(f"    주요 카테고리: {cat['is_primary']}")
                print(f"    출처: {cat['source']}")
                print()
        
        # 3. 키워드 확인
        print("\n[3] 등록된 키워드")
        print("-" * 80)
        keywords = await database.fetch_all(
            """
            SELECT 
                id,
                keyword,
                match_type,
                priority,
                source
            FROM advertiser_keywords
            WHERE advertiser_id = :advertiser_id
            ORDER BY priority DESC, match_type
            """
            , {"advertiser_id": advertiser_id}
        )
        
        if not keywords:
            print("❌ 등록된 키워드가 없습니다.")
        else:
            print(f"총 {len(keywords)}개의 키워드:")
            for kw in keywords:
                print(f"  - {kw['keyword']} ({kw['match_type']}, 우선순위: {kw['priority']})")
        
        # 4. 자동 입찰 설정
        print("\n[4] 자동 입찰 설정 (매칭 필수!)")
        print("-" * 80)
        auto_bid = await database.fetch_one(
            """
            SELECT 
                id,
                is_enabled,
                daily_budget,
                max_bid_per_keyword,
                min_quality_score,
                preferred_categories
            FROM auto_bid_settings
            WHERE advertiser_id = :advertiser_id
            """
            , {"advertiser_id": advertiser_id}
        )
        
        if not auto_bid:
            print("❌ 자동 입찰 설정이 없습니다. (매칭 불가능!)")
        else:
            print(f"활성화 여부: {'✅ 활성화' if auto_bid['is_enabled'] else '❌ 비활성화 (매칭 안됨!)'}")
            print(f"일일 예산: {auto_bid['daily_budget']}")
            print(f"최대 입찰가: {auto_bid['max_bid_per_keyword']}")
            print(f"최소 품질 점수: {auto_bid['min_quality_score']}")
            print(f"선호 카테고리: {auto_bid['preferred_categories']}")
        
        # 5. 심사 상태
        print("\n[5] 광고주 심사 상태")
        print("-" * 80)
        review = await database.fetch_one(
            """
            SELECT 
                id,
                review_status,
                recommended_bid_min,
                recommended_bid_max
            FROM advertiser_reviews
            WHERE advertiser_id = :advertiser_id
            """
            , {"advertiser_id": advertiser_id}
        )
        
        if not review:
            print("⚠️ 심사 상태가 없습니다.")
        else:
            status_icon = "✅" if review['review_status'] == 'approved' else "❌"
            print(f"심사 상태: {status_icon} {review['review_status']}")
            print(f"권장 최소 입찰가: {review['recommended_bid_min']}")
            print(f"권장 최대 입찰가: {review['recommended_bid_max']}")
        
        # 6. 종합 진단
        print("\n" + "=" * 80)
        print("[종합 진단]")
        print("=" * 80)
        
        issues = []
        
        if not advertiser['category']:
            issues.append("❌ 표준 카테고리(advertisers.category)가 설정되지 않음")
        
        if not categories:
            issues.append("⚠️ 비즈니스 카테고리(advertiser_categories)가 설정되지 않음")
        
        if not keywords:
            issues.append("❌ 키워드가 등록되지 않음 (매칭 불가능!)")
        
        if not auto_bid:
            issues.append("❌ 자동 입찰 설정이 없음 (매칭 불가능!)")
        elif not auto_bid['is_enabled']:
            issues.append("❌ 자동 입찰이 비활성화됨 (매칭 안됨!)")
        
        if not review or review['review_status'] != 'approved':
            issues.append("⚠️ 심사가 승인되지 않음")
        
        if issues:
            print("발견된 문제점:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("✅ 모든 설정이 정상입니다!")
        
        # 7. 해결 방법 제시
        print("\n" + "=" * 80)
        print("[해결 방법]")
        print("=" * 80)
        
        if not advertiser['category']:
            print("\n1. 표준 카테고리 설정:")
            print("   UPDATE advertisers SET category = '서비스' WHERE id = :id;")
            print("   (한화생명은 보험 회사이므로 '서비스' 카테고리가 적합)")
        
        if not auto_bid or not auto_bid['is_enabled']:
            print("\n2. 자동 입찰 활성화:")
            if not auto_bid:
                print("   INSERT INTO auto_bid_settings (advertiser_id, is_enabled, daily_budget, max_bid_per_keyword, min_quality_score)")
                print("   VALUES (:id, true, 10000, 3000, 50);")
            else:
                print("   UPDATE auto_bid_settings SET is_enabled = true WHERE advertiser_id = :id;")
        
        if not keywords:
            print("\n3. 키워드 등록 필요:")
            print("   INSERT INTO advertiser_keywords (advertiser_id, keyword, match_type, priority)")
            print("   VALUES (:id, '생명보험', 'exact', 5),")
            print("          (:id, '보험', 'broad', 3),")
            print("          (:id, '한화생명', 'exact', 5);")
        
        if not review or review['review_status'] != 'approved':
            print("\n4. 심사 승인 필요:")
            if not review:
                print("   INSERT INTO advertiser_reviews (advertiser_id, review_status)")
                print("   VALUES (:id, 'approved');")
            else:
                print("   UPDATE advertiser_reviews SET review_status = 'approved' WHERE advertiser_id = :id;")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(check_hanwha_advertiser())

