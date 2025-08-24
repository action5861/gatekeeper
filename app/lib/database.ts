import { Pool } from 'pg'

// 데이터베이스 연결 풀 설정
const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'gatekeeper',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'password',
    max: 20, // 최대 연결 수
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
})

// 데이터베이스 연결 테스트
export async function testConnection() {
    try {
        const client = await pool.connect()
        await client.query('SELECT NOW()')
        client.release()
        return true
    } catch (error) {
        console.error('데이터베이스 연결 실패:', error)
        return false
    }
}

// 카테고리 인터페이스
export interface DBCategory {
    id: number
    parent_id: number | null
    name: string
    path: string
    level: number
    is_active: boolean
    sort_order: number
    created_at: Date
}

export interface CategoryTree {
    id: number
    name: string
    path: string
    level: number
    children?: CategoryTree[]
}

// 플랫 데이터를 트리 구조로 변환
export function buildCategoryTree(categories: DBCategory[]): CategoryTree[] {
    const categoryMap = new Map<number, CategoryTree>()
    const rootCategories: CategoryTree[] = []

    // 모든 카테고리를 맵에 추가
    categories.forEach(category => {
        categoryMap.set(category.id, {
            id: category.id,
            name: category.name,
            path: category.path,
            level: category.level,
            children: []
        })
    })

    // 부모-자식 관계 설정
    categories.forEach(category => {
        const treeNode = categoryMap.get(category.id)!

        if (category.parent_id === null) {
            // 루트 카테고리
            rootCategories.push(treeNode)
        } else {
            // 자식 카테고리
            const parentNode = categoryMap.get(category.parent_id)
            if (parentNode) {
                if (!parentNode.children) {
                    parentNode.children = []
                }
                parentNode.children.push(treeNode)
            }
        }
    })

    // 정렬 (sort_order 기준)
    const sortCategories = (cats: CategoryTree[]): CategoryTree[] => {
        return cats.sort((a, b) => {
            const aOrder = categories.find(c => c.id === a.id)?.sort_order || 0
            const bOrder = categories.find(c => c.id === b.id)?.sort_order || 0
            return aOrder - bOrder
        }).map(cat => ({
            ...cat,
            children: cat.children ? sortCategories(cat.children) : undefined
        }))
    }

    return sortCategories(rootCategories)
}

// 비즈니스 카테고리 조회
export async function getBusinessCategories(
    search?: string,
    level?: number,
    parentId?: number
): Promise<DBCategory[]> {
    const client = await pool.connect()

    try {
        let query = `
            SELECT id, parent_id, name, path, level, is_active, sort_order, created_at
            FROM business_categories 
            WHERE is_active = true
        `
        const params: any[] = []
        let paramIndex = 1

        // 검색 조건
        if (search) {
            query += ` AND (name ILIKE $${paramIndex} OR path ILIKE $${paramIndex})`
            params.push(`%${search}%`)
            paramIndex++
        }

        // 레벨 필터
        if (level) {
            query += ` AND level = $${paramIndex}`
            params.push(level)
            paramIndex++
        }

        // 부모 ID 필터
        if (parentId !== undefined) {
            if (parentId === null) {
                query += ` AND parent_id IS NULL`
            } else {
                query += ` AND parent_id = $${paramIndex}`
                params.push(parentId)
                paramIndex++
            }
        }

        query += ` ORDER BY sort_order, name`

        const result = await client.query(query, params)
        return result.rows
    } finally {
        client.release()
    }
}

// 카테고리 트리 조회
export async function getCategoryTree(
    search?: string,
    level?: number
): Promise<CategoryTree[]> {
    const categories = await getBusinessCategories(search, level)
    return buildCategoryTree(categories)
}

// 특정 카테고리 조회
export async function getCategoryById(id: number): Promise<DBCategory | null> {
    const client = await pool.connect()

    try {
        const result = await client.query(
            'SELECT id, parent_id, name, path, level, is_active, sort_order, created_at FROM business_categories WHERE id = $1 AND is_active = true',
            [id]
        )
        return result.rows[0] || null
    } finally {
        client.release()
    }
}

// 카테고리 추가
export async function addCategory(
    name: string,
    parentId: number | null,
    level: number
): Promise<DBCategory> {
    const client = await pool.connect()

    try {
        // 경로 생성
        let path = name
        if (parentId) {
            const parent = await getCategoryById(parentId)
            if (parent) {
                path = `${parent.path} > ${name}`
            }
        }

        const result = await client.query(
            `INSERT INTO business_categories (name, parent_id, path, level, sort_order)
             VALUES ($1, $2, $3, $4, 
                     (SELECT COALESCE(MAX(sort_order), 0) + 1 
                      FROM business_categories 
                      WHERE parent_id = $2))
             RETURNING id, parent_id, name, path, level, is_active, sort_order, created_at`,
            [name, parentId, path, level]
        )

        return result.rows[0]
    } finally {
        client.release()
    }
}

// 카테고리 업데이트
export async function updateCategory(
    id: number,
    updates: Partial<Pick<DBCategory, 'name' | 'is_active' | 'sort_order'>>
): Promise<DBCategory | null> {
    const client = await pool.connect()

    try {
        const setClauses: string[] = []
        const values: any[] = []
        let paramIndex = 1

        if (updates.name !== undefined) {
            setClauses.push(`name = $${paramIndex}`)
            values.push(updates.name)
            paramIndex++
        }

        if (updates.is_active !== undefined) {
            setClauses.push(`is_active = $${paramIndex}`)
            values.push(updates.is_active)
            paramIndex++
        }

        if (updates.sort_order !== undefined) {
            setClauses.push(`sort_order = $${paramIndex}`)
            values.push(updates.sort_order)
            paramIndex++
        }

        if (setClauses.length === 0) {
            return null
        }

        values.push(id)
        const result = await client.query(
            `UPDATE business_categories 
             SET ${setClauses.join(', ')}, updated_at = CURRENT_TIMESTAMP
             WHERE id = $${paramIndex}
             RETURNING id, parent_id, name, path, level, is_active, sort_order, created_at`,
            values
        )

        return result.rows[0] || null
    } finally {
        client.release()
    }
}

// 카테고리 삭제 (논리적 삭제)
export async function deleteCategory(id: number): Promise<boolean> {
    const client = await pool.connect()

    try {
        const result = await client.query(
            'UPDATE business_categories SET is_active = false WHERE id = $1',
            [id]
        )
        return result.rowCount > 0
    } finally {
        client.release()
    }
}

// 연결 풀 종료
export async function closePool() {
    await pool.end()
} 