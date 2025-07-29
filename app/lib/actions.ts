'use server'

// 서버 액션 (데이터 페칭 등)

interface AuthData {
    userType: 'user' | 'advertiser'
    email: string
    password: string
    username?: string
    companyName?: string
}

interface LoginResponse {
    access_token: string
    token_type: string
}

interface RegisterResponse {
    success: boolean
    message: string
    username?: string
    access_token?: string
}

export async function login(data: AuthData): Promise<LoginResponse> {
    try {
        const serviceUrl = data.userType === 'advertiser'
            ? process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'
            : process.env.USER_SERVICE_URL || 'http://localhost:8005'

        const response = await fetch(`${serviceUrl}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: data.email, // Using email as username for now
                password: data.password,
            }),
        })

        if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Login failed')
        }

        return await response.json()
    } catch (error) {
        console.error('Login error:', error)
        throw new Error(error instanceof Error ? error.message : 'Login failed')
    }
}

export async function register(data: AuthData): Promise<RegisterResponse> {
    try {
        const serviceUrl = data.userType === 'advertiser'
            ? process.env.ADVERTISER_SERVICE_URL || 'http://localhost:8007'
            : process.env.USER_SERVICE_URL || 'http://localhost:8005'

        const requestBody = data.userType === 'advertiser'
            ? {
                username: data.username,
                email: data.email,
                password: data.password,
                company_name: data.companyName,
            }
            : {
                username: data.username,
                email: data.email,
                password: data.password,
            }

        const response = await fetch(`${serviceUrl}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        })

        if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Registration failed')
        }

        return await response.json()
    } catch (error) {
        console.error('Registration error:', error)
        throw new Error(error instanceof Error ? error.message : 'Registration failed')
    }
} 