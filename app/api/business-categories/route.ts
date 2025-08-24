import { addCategory, getBusinessCategories, getCategoryById } from '@/lib/database'
import { NextRequest, NextResponse } from 'next/server'

// 광고주 서비스에서 직접 카테고리를 가져와 프론트와 동일한 소스 사용
const getAdvertiserServiceCategories = async () => {
    const serviceUrl = process.env.ADVERTISER_SERVICE_URL || 'http://advertiser-service:8007'
    const res = await fetch(`${serviceUrl}/business-categories`)
    if (!res.ok) throw new Error(`Advertiser service categories fetch failed: ${res.status}`)
    return await res.json()
}

interface Category {
    id: number
    name: string
    path: string
    level: number
    children?: Category[]
}

// 실제 프로덕션에서는 데이터베이스에서 가져와야 합니다
const businessCategories: Category[] = [
    {
        id: 1,
        name: '전자제품',
        path: '전자제품',
        level: 1,
        children: [
            { id: 11, name: '스마트폰', path: '전자제품 > 스마트폰', level: 2 },
            { id: 12, name: '노트북', path: '전자제품 > 노트북', level: 2 },
            { id: 13, name: '태블릿', path: '전자제품 > 태블릿', level: 2 },
            { id: 14, name: '데스크톱', path: '전자제품 > 데스크톱', level: 2 },
            { id: 15, name: '모니터', path: '전자제품 > 모니터', level: 2 },
            { id: 16, name: '키보드/마우스', path: '전자제품 > 키보드/마우스', level: 2 },
            { id: 17, name: '스피커/헤드폰', path: '전자제품 > 스피커/헤드폰', level: 2 },
            { id: 18, name: '카메라', path: '전자제품 > 카메라', level: 2 }
        ]
    },
    {
        id: 2,
        name: '패션',
        path: '패션',
        level: 1,
        children: [
            { id: 21, name: '남성의류', path: '패션 > 남성의류', level: 2 },
            { id: 22, name: '여성의류', path: '패션 > 여성의류', level: 2 },
            { id: 23, name: '신발', path: '패션 > 신발', level: 2 },
            { id: 24, name: '가방', path: '패션 > 가방', level: 2 },
            { id: 25, name: '액세서리', path: '패션 > 액세서리', level: 2 },
            { id: 26, name: '언더웨어', path: '패션 > 언더웨어', level: 2 },
            { id: 27, name: '스포츠웨어', path: '패션 > 스포츠웨어', level: 2 }
        ]
    },
    {
        id: 3,
        name: '뷰티',
        path: '뷰티',
        level: 1,
        children: [
            { id: 31, name: '스킨케어', path: '뷰티 > 스킨케어', level: 2 },
            { id: 32, name: '메이크업', path: '뷰티 > 메이크업', level: 2 },
            { id: 33, name: '헤어케어', path: '뷰티 > 헤어케어', level: 2 },
            { id: 34, name: '향수', path: '뷰티 > 향수', level: 2 },
            { id: 35, name: '네일케어', path: '뷰티 > 네일케어', level: 2 },
            { id: 36, name: '남성화장품', path: '뷰티 > 남성화장품', level: 2 }
        ]
    },
    {
        id: 4,
        name: '홈&리빙',
        path: '홈&리빙',
        level: 1,
        children: [
            { id: 41, name: '가구', path: '홈&리빙 > 가구', level: 2 },
            { id: 42, name: '침구', path: '홈&리빙 > 침구', level: 2 },
            { id: 43, name: '조명', path: '홈&리빙 > 조명', level: 2 },
            { id: 44, name: '주방용품', path: '홈&리빙 > 주방용품', level: 2 },
            { id: 45, name: '욕실용품', path: '홈&리빙 > 욕실용품', level: 2 },
            { id: 46, name: '청소용품', path: '홈&리빙 > 청소용품', level: 2 },
            { id: 47, name: '인테리어소품', path: '홈&리빙 > 인테리어소품', level: 2 }
        ]
    },
    {
        id: 5,
        name: '스포츠&레저',
        path: '스포츠&레저',
        level: 1,
        children: [
            { id: 51, name: '운동복', path: '스포츠&레저 > 운동복', level: 2 },
            { id: 52, name: '운동화', path: '스포츠&레저 > 운동화', level: 2 },
            { id: 53, name: '스포츠용품', path: '스포츠&레저 > 스포츠용품', level: 2 },
            { id: 54, name: '등산용품', path: '스포츠&레저 > 등산용품', level: 2 },
            { id: 55, name: '캠핑용품', path: '스포츠&레저 > 캠핑용품', level: 2 },
            { id: 56, name: '자전거', path: '스포츠&레저 > 자전거', level: 2 },
            { id: 57, name: '골프용품', path: '스포츠&레저 > 골프용품', level: 2 }
        ]
    },
    {
        id: 6,
        name: '도서&문구',
        path: '도서&문구',
        level: 1,
        children: [
            { id: 61, name: '도서', path: '도서&문구 > 도서', level: 2 },
            { id: 62, name: '문구용품', path: '도서&문구 > 문구용품', level: 2 },
            { id: 63, name: '오피스용품', path: '도서&문구 > 오피스용품', level: 2 },
            { id: 64, name: '학습용품', path: '도서&문구 > 학습용품', level: 2 },
            { id: 65, name: '미술용품', path: '도서&문구 > 미술용품', level: 2 }
        ]
    },
    {
        id: 7,
        name: '식품&음료',
        path: '식품&음료',
        level: 1,
        children: [
            { id: 71, name: '신선식품', path: '식품&음료 > 신선식품', level: 2 },
            { id: 72, name: '가공식품', path: '식품&음료 > 가공식품', level: 2 },
            { id: 73, name: '음료', path: '식품&음료 > 음료', level: 2 },
            { id: 74, name: '건강식품', path: '식품&음료 > 건강식품', level: 2 },
            { id: 75, name: '간식', path: '식품&음료 > 간식', level: 2 },
            { id: 76, name: '조미료', path: '식품&음료 > 조미료', level: 2 }
        ]
    },
    {
        id: 8,
        name: '자동차',
        path: '자동차',
        level: 1,
        children: [
            { id: 81, name: '자동차용품', path: '자동차 > 자동차용품', level: 2 },
            { id: 82, name: '오토바이용품', path: '자동차 > 오토바이용품', level: 2 },
            { id: 83, name: '자동차부품', path: '자동차 > 자동차부품', level: 2 },
            { id: 84, name: '자동차정비', path: '자동차 > 자동차정비', level: 2 }
        ]
    },
    {
        id: 9,
        name: '유아용품',
        path: '유아용품',
        level: 1,
        children: [
            { id: 91, name: '유아의류', path: '유아용품 > 유아의류', level: 2 },
            { id: 92, name: '유아용품', path: '유아용품 > 유아용품', level: 2 },
            { id: 93, name: '유아식품', path: '유아용품 > 유아식품', level: 2 },
            { id: 94, name: '유아완구', path: '유아용품 > 유아완구', level: 2 },
            { id: 95, name: '유아도서', path: '유아용품 > 유아도서', level: 2 }
        ]
    },
    {
        id: 10,
        name: '반려동물',
        path: '반려동물',
        level: 1,
        children: [
            { id: 101, name: '강아지용품', path: '반려동물 > 강아지용품', level: 2 },
            { id: 102, name: '고양이용품', path: '반려동물 > 고양이용품', level: 2 },
            { id: 103, name: '반려동물식품', path: '반려동물 > 반려동물식품', level: 2 },
            { id: 104, name: '반려동물용품', path: '반려동물 > 반려동물용품', level: 2 }
        ]
    }
]

export async function GET(request: NextRequest) {
    try {
        // 실제 프로덕션에서는 데이터베이스 쿼리나 외부 API 호출을 수행합니다
        // 여기서는 시뮬레이션을 위해 약간의 지연을 추가합니다
        await new Promise(resolve => setTimeout(resolve, 100))

        // 검색 파라미터 처리 (선택사항)
        const { searchParams } = new URL(request.url)
        const search = searchParams.get('search')
        const level = searchParams.get('level')

        // 1) 광고주 서비스에서 플랫 구조 조회
        try {
            const flatFromService = await getAdvertiserServiceCategories()
            // 서비스가 이미 플랫 배열을 주므로 그대로 반환
            return NextResponse.json({
                success: true,
                categories: flatFromService,
                total: Array.isArray(flatFromService) ? flatFromService.length : (flatFromService?.length || 0),
                timestamp: new Date().toISOString(),
                source: 'advertiser-service'
            })
        } catch (svcErr) {
            console.warn('광고주 서비스 조회 실패, 로컬 DB 시도:', svcErr)
            // 2) 로컬 DB에서 플랫 조회
            try {
                const flat = await getBusinessCategories(search || undefined, level ? parseInt(level) : undefined)
                return NextResponse.json({
                    success: true,
                    categories: flat,
                    total: flat.length,
                    timestamp: new Date().toISOString(),
                    source: 'database'
                })
            } catch (dbError) {
                console.error('데이터베이스 조회 실패, 폴백 데이터 사용:', dbError)

                // 3) 폴백: 트리 → 플랫 변환 후 반환
                const flatFromTree: Array<{ id: number; parent_id: number | null; name: string; path: string; level: number }> = []

                const walk = (nodes: Category[], parentId: number | null) => {
                    nodes.forEach((node) => {
                        flatFromTree.push({
                            id: node.id,
                            parent_id: parentId,
                            name: node.name,
                            path: node.path,
                            level: node.level,
                        })
                        if (node.children && node.children.length) {
                            walk(node.children, node.id)
                        }
                    })
                }
                walk(businessCategories, null)

                // 간단한 필터링 적용
                let filtered = flatFromTree
                if (search) {
                    const q = search.toLowerCase()
                    filtered = filtered.filter((c) => c.name.toLowerCase().includes(q) || c.path.toLowerCase().includes(q))
                }
                if (level) {
                    const levelNum = parseInt(level)
                    filtered = filtered.filter((c) => c.level === levelNum)
                }

                return NextResponse.json({
                    success: true,
                    categories: filtered,
                    total: filtered.length,
                    timestamp: new Date().toISOString(),
                    source: 'fallback'
                })
            }
        }

    } catch (error) {
        console.error('카테고리 조회 에러:', error)

        return NextResponse.json(
            {
                success: false,
                error: '카테고리를 불러오는데 실패했습니다',
                message: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다'
            },
            { status: 500 }
        )
    }
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()

        // 입력 검증
        if (!body.name || typeof body.name !== 'string') {
            return NextResponse.json(
                {
                    success: false,
                    error: '카테고리 이름이 필요합니다'
                },
                { status: 400 }
            )
        }

        if (!body.level || typeof body.level !== 'number' || body.level < 1 || body.level > 3) {
            return NextResponse.json(
                {
                    success: false,
                    error: '유효한 레벨(1-3)이 필요합니다'
                },
                { status: 400 }
            )
        }

        // 부모 카테고리 검증
        if (body.parentId !== undefined && body.parentId !== null) {
            const parentCategory = await getCategoryById(body.parentId)
            if (!parentCategory) {
                return NextResponse.json(
                    {
                        success: false,
                        error: '존재하지 않는 부모 카테고리입니다'
                    },
                    { status: 400 }
                )
            }
        }

        // 실제 데이터베이스에 카테고리 추가
        const newCategory = await addCategory(
            body.name,
            body.parentId || null,
            body.level
        )

        return NextResponse.json({
            success: true,
            message: '카테고리가 성공적으로 추가되었습니다',
            category: newCategory,
            timestamp: new Date().toISOString()
        })

    } catch (error) {
        console.error('카테고리 추가 에러:', error)

        return NextResponse.json(
            {
                success: false,
                error: '카테고리 추가에 실패했습니다',
                message: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다'
            },
            { status: 500 }
        )
    }
} 