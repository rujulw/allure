'use client'

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, clearTokens, setTokens } from '@/lib/api'
import type { UserRead, LoginRequest, RegisterRequest, TokenPair } from '@/types/auth'

interface AuthState {
  user: UserRead | null
  isLoading: boolean
  isAuthenticated: boolean
}

interface AuthActions {
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<UserRead>
  logout: () => void
}

type AuthContextValue = AuthState & AuthActions

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setIsLoading(false)
      return
    }

    api
      .get<UserRead>('/auth/me')
      .then(setUser)
      .catch(() => {
        clearTokens()
      })
      .finally(() => setIsLoading(false))
  }, [])

  async function login(data: LoginRequest): Promise<void> {
    const tokens = await api.post<TokenPair>('/auth/login', data)
    setTokens(tokens.access_token, tokens.refresh_token)
    const me = await api.get<UserRead>('/auth/me')
    setUser(me)
  }

  async function register(data: RegisterRequest): Promise<UserRead> {
    return api.post<UserRead>('/auth/register', data)
  }

  function logout(): void {
    clearTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider')
  return ctx
}
