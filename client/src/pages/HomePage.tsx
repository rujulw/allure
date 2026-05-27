import { motion } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'

export function HomePage() {
  const { user } = useAuth()

  return (
    <div className="flex min-h-full items-center justify-center px-8 py-20">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="space-y-4 text-center"
      >
        <p className="text-[11px] tracking-[0.12em] text-[#333] lowercase">
          signed in as {user?.email}
        </p>
        <h1 className="text-2xl font-medium tracking-[-0.03em] text-[#f0f0f0]">
          under construction
        </h1>
      </motion.div>
    </div>
  )
}
