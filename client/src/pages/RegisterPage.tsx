import { useState } from 'react'
import { Link } from 'react-router'
import { motion } from 'framer-motion'
import { useRegisterForm } from '@/hooks/useAuth'

const fieldVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.07, duration: 0.35, ease: [0.16, 1, 0.3, 1] },
  }),
}

export function RegisterPage() {
  const { submit, error, isSubmitting } = useRegisterForm()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [confirmError, setConfirmError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (password !== confirm) {
      setConfirmError('Passwords do not match')
      return
    }
    setConfirmError(null)
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
          {(['♣', '♥', '♠', '♦'] as const).map((s, i) => (
            <span
              key={s}
              className="select-none text-7xl"
              style={{ color: i % 2 === 0 ? '#1a1a1a' : '#c0392b' }}
            >
              {s}
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
              Create account
            </h1>
            <p className="text-sm text-[#555]">Take a seat at the table</p>
          </div>

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
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-sm border border-white/[0.07] bg-[#111] px-3.5 py-2.5 text-sm text-[#f0f0f0] outline-none placeholder:text-[#333] transition-all duration-150 focus:border-[#e2c97e]/40 focus:shadow-[0_0_0_3px_rgba(226,201,126,0.06)]"
                placeholder="min. 8 characters"
              />
            </motion.div>

            <motion.div custom={2} variants={fieldVariants} initial="hidden" animate="visible" className="space-y-1.5">
              <label className="block text-[11px] tracking-[0.06em] text-[#555] uppercase">
                Confirm password
              </label>
              <input
                type="password"
                autoComplete="new-password"
                required
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="w-full rounded-sm border border-white/[0.07] bg-[#111] px-3.5 py-2.5 text-sm text-[#f0f0f0] outline-none placeholder:text-[#333] transition-all duration-150 focus:border-[#e2c97e]/40 focus:shadow-[0_0_0_3px_rgba(226,201,126,0.06)]"
                placeholder="••••••••"
              />
              {confirmError && (
                <p className="text-xs text-red-400/80">{confirmError}</p>
              )}
            </motion.div>

            {error && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-xs text-red-400/80">
                {error}
              </motion.p>
            )}

            <motion.div custom={3} variants={fieldVariants} initial="hidden" animate="visible">
              <button
                type="submit"
                disabled={isSubmitting}
                className="mt-1 w-full rounded-sm bg-[#e2c97e] px-4 py-2.5 text-sm font-medium tracking-[-0.01em] text-[#0a0a0a] transition-all duration-150 hover:bg-[#d4bc72] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating account...' : 'Create account'}
              </button>
            </motion.div>
          </form>

          <motion.p
            custom={4}
            variants={fieldVariants}
            initial="hidden"
            animate="visible"
            className="text-xs text-[#444]"
          >
            Already have an account?{' '}
            <Link to="/login" className="text-[#777] underline-offset-2 hover:text-[#f0f0f0] hover:underline transition-colors duration-150">
              Sign in
            </Link>
          </motion.p>
        </div>
      </motion.div>
    </div>
  )
}
