import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useAuthContext } from '@/contexts/AuthContext'
import { ApiError } from '@/lib/api'
import type { LoginRequest, RegisterRequest } from '@/types/auth'

export function useAuth() {
  return useAuthContext()
}

export function useLoginForm() {
  const { login } = useAuthContext()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function submit(data: LoginRequest): Promise<void> {
    setError(null)
    setIsSubmitting(true)
    try {
      await login(data)
      navigate('/', { replace: true })
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong')
    } finally {
      setIsSubmitting(false)
    }
  }

  return { submit, error, isSubmitting }
}

export function useRegisterForm() {
  const { register } = useAuthContext()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function submit(data: RegisterRequest): Promise<void> {
    setError(null)
    setIsSubmitting(true)
    try {
      await register(data)
      navigate('/login', { replace: true, state: { registered: true } })
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong')
    } finally {
      setIsSubmitting(false)
    }
  }

  return { submit, error, isSubmitting }
}
