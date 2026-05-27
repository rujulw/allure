import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { AuthProvider } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

beforeEach(() => {
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('ProtectedRoute', () => {
  it('redirects unauthenticated users to /login', async () => {
    render(
      <QueryClientProvider client={makeQueryClient()}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path="/login" element={<div>login page</div>} />
              <Route element={<ProtectedRoute />}>
                <Route index element={<div>protected</div>} />
              </Route>
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('login page')).toBeInTheDocument()
    })
  })

  it('renders children when token resolves to a valid user', async () => {
    localStorage.setItem('access_token', 'valid-token')

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ id: 1, email: 'test@example.com' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    render(
      <QueryClientProvider client={makeQueryClient()}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/']}>
            <Routes>
              <Route path="/login" element={<div>login page</div>} />
              <Route element={<ProtectedRoute />}>
                <Route index element={<div>protected content</div>} />
              </Route>
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('protected content')).toBeInTheDocument()
    })
  })
})
