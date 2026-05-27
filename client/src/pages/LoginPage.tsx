import { useState } from 'react'
import { Link, useLocation } from 'react-router'
import { motion } from 'framer-motion'
import { useLoginForm } from '@/hooks/useAuth'

const SUITS = [
  { symbol: '♣', color: '#1a1a1a' },
  { symbol: '♥', color: '#c0392b' },
  { symbol: '♠', color: '#1a1a1a' },
  { symbol: '♦', color: '#c0392b' },
]

const fieldVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.07, duration: 0.35, ease: [0.16, 1, 0.3, 1] },
  }),
}

export function LoginPage() {
  const { submit, error, isSubmitting } = useLoginForm()
  const location = useLocation()
  const registered = (location.state as { registered?: boolean } | null)?.registered

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    void submit({ email, password })
  }

  return (
    <div className="flex min-h-[100dvh] bg-[#0a0a0a]">
      {/* Left brand panel */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative hidden flex-col justify-between bg-[#e8e8e8] px-10 py-10 lg:flex lg:w-[42%]"
      >
        <span className="text-4xl font-semibold tracking-[-0.02em] text-[#0f0f0f]">
          allure
        </span>

        <div className="flex items-center justify-center gap-7">
          {SUITS.map(({ symbol, color }) => (
            <span
              key={symbol}
              className="select-none text-7xl"
              style={{ color }}
            >
              {symbol}
            </span>
          ))}
        </div>

        <div />
      </motion.div>

      {/* Right form panel */}
      <motion.div
        initial={{ opacity: 0, x: 16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        className="flex flex-1 items-center justify-center px-6 py-12"
      >
        <div className="w-full max-w-[360px] space-y-8">
          <div className="space-y-1">
            <h1 className="text-xl font-medium tracking-[-0.02em] text-[#f0f0f0]">
              Welcome back
            </h1>
            <p className="text-sm text-[#555]">Sign in to your account</p>
          </div>

          {registered && (
            <motion.p
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-xs text-[#e2c97e]"
            >
              Account created — sign in to continue.
            </motion.p>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <motion.div custom={0} variants={fieldVariants} initial="hidden" animate="visible" className="space-y-1.5">
              <label className="block text-[11px] tracking-[0.06em] text-[#555] uppercase">
                Email
              </label>
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-sm border border-white/[0.07] bg-[#111] px-3.5 py-2.5 text-sm text-[#f0f0f0] outline-none placeholder:text-[#333] transition-all duration-150 focus:border-[#e2c97e]/40 focus:shadow-[0_0_0_3px_rgba(226,201,126,0.06)]"
                placeholder="you@example.com"
              />
            </motion.div>

            <motion.div custom={1} variants={fieldVariants} initial="hidden" animate="visible" className="space-y-1.5">
              <label className="block text-[11px] tracking-[0.06em] text-[#555] uppercase">
                Password
              </label>
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-sm border border-white/[0.07] bg-[#111] px-3.5 py-2.5 text-sm text-[#f0f0f0] outline-none placeholder:text-[#333] transition-all duration-150 focus:border-[#e2c97e]/40 focus:shadow-[0_0_0_3px_rgba(226,201,126,0.06)]"
                placeholder="••••••••"
              />
            </motion.div>

            {error && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-xs text-red-400/80"
              >
                {error}
              </motion.p>
            )}

            <motion.div custom={2} variants={fieldVariants} initial="hidden" animate="visible">
              <button
                type="submit"
                disabled={isSubmitting}
                className="mt-1 w-full rounded-sm bg-[#e2c97e] px-4 py-2.5 text-sm font-medium tracking-[-0.01em] text-[#0a0a0a] transition-all duration-150 hover:bg-[#d4bc72] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Signing in...' : 'Sign in'}
              </button>
            </motion.div>
          </form>

          <motion.p
            custom={3}
            variants={fieldVariants}
            initial="hidden"
            animate="visible"
            className="text-xs text-[#444]"
          >
            No account?{' '}
            <Link to="/register" className="text-[#777] underline-offset-2 hover:text-[#f0f0f0] hover:underline transition-colors duration-150">
              Register
            </Link>
          </motion.p>
        </div>
      </motion.div>
    </div>
  )
}
