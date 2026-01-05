#!/usr/bin/env python3
"""하이마트 광고주 카테고리 확인 스크립트"""
import asyncio
import os
from databases import Database

# 데이터베이스 연결 정보
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:your_secure_password_123@localhost:5433/search_exchange_db",
)

database = Database(DATABASE_URL)

async def check_himart_categories():
    """하이마트 광고주의 카테고리 정보 확인"""
    await database.connect()
    
    try:
        # 1. 하이마트 광고주 찾기
        print("\n[1] 하이마트 광고주 정보")
        print("=" * 80)
        advertisers = await database.fetch_all(
            """
            SELECT 
                id,
                username,
                email,
                company_name,
                category,
                approval_status,
                website_url
            FROM advertisers
            WHERE company_name ILIKE '%하이마트%' 
               OR company_name ILIKE '%HI-MART%'
               OR company_name ILIKE '%himart%'
            ORDER BY id
            """
        )
        
        if not advertisers:
            print("❌ 하이마트 광고주를 찾을 수 없습니다.")
            return
        
        for adv in advertisers:
            print(f"\n광고주 ID: {adv['id']}")
            print(f"회사명: {adv['company_name']}")
            print(f"이메일: {adv['email']}")
            print(f"사용자명: {adv['username']}")
            print(f"advertisers.category 컬럼: {adv['category']}")
            print(f"웹사이트: {adv['website_url']}")
            print(f"승인 상태: {adv['approval_status']}")
            
            advertiser_id = adv['id']
            
            # 2. 카테고리 조회
            print(f"\n[2] 광고주 ID {advertiser_id}의 카테고리 목록")
            print("=" * 80)
            categories = await database.fetch_all(
                """
                SELECT 
                    ac.id,
                    ac.category_path,
                    ac.category_level,
                    ac.is_primary,
                    ac.source,
                    ac.created_at,
                    bc.name as category_name
                FROM advertiser_categories ac
                LEFT JOIN business_categories bc ON ac.category_path = bc.path
                WHERE ac.advertiser_id = :advertiser_id
                ORDER BY ac.is_primary DESC, ac.category_level ASC, ac.category_path ASC
                """,
                {"advertiser_id": advertiser_id}
            )
            
            if not categories:
                print("❌ 등록된 카테고리가 없습니다.")
            else:
                print(f"총 {len(categories)}개의 카테고리:")
                for cat in categories:
                    primary_mark = "⭐ [PRIMARY]" if cat['is_primary'] else "  "
                    source = cat.get('source', 'unknown')
                    print(f"{primary_mark} {cat['category_path']}")
                    if cat['category_name']:
                        print(f"     이름: {cat['category_name']}")
                    print(f"     레벨: {cat['category_level']}")
                    print(f"     출처: {source}")
                    print(f"     생성일: {cat['created_at']}")
                    print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(check_himart_categories())

