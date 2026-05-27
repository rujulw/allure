import { Outlet } from 'react-router'
import { Navbar } from './Navbar'

export function AppShell() {
  return (
    <div className="flex h-full flex-col bg-[#0a0a0a]">
      <Navbar />
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
