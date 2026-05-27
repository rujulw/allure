import { useAuth } from '@/hooks/useAuth'

export function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="flex items-center justify-between border-b border-white/[0.04] px-8 py-4">
      <span className="text-4xl font-semibold tracking-[-0.02em] text-[#f0f0f0]">
        allure
      </span>
      <div className="flex items-center gap-6">
        <span className="text-xs text-[#444]">{user?.email}</span>
        <button
          onClick={logout}
          className="text-xs text-[#555] transition-colors duration-150 hover:text-[#f0f0f0]"
        >
          sign out
        </button>
      </div>
    </header>
  )
}
