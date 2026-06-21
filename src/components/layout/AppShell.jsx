import { AudioLines, Clock3, Home, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'

const nav = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/history', label: 'History', icon: Clock3 },
]

export function AppShell({ children }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="min-h-screen bg-canvas">
      <header className="sticky top-0 z-40 border-b border-[#e9eaf1]/90 bg-canvas/90 backdrop-blur-xl">
        <div className="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-5 sm:px-8">
          <Link to="/" className="flex items-center gap-3" aria-label="Voxly home">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-primary text-white shadow-lg shadow-primary/20"><AudioLines size={21} /></span>
            <span className="font-display text-xl font-extrabold tracking-tight">Voxly<span className="text-primary">.</span></span>
          </Link>
          <nav className="hidden items-center gap-2 sm:flex">
            {nav.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${isActive ? 'bg-primary/10 text-primary' : 'text-muted hover:text-ink'}`}><Icon size={17}/>{label}</NavLink>)}
            <Link to="/conversation" className="ml-3 rounded-xl bg-ink px-4 py-2.5 text-sm font-bold text-white transition hover:bg-primary">New conversation</Link>
          </nav>
          <button className="grid h-10 w-10 place-items-center rounded-xl bg-white sm:hidden" onClick={() => setOpen(!open)} aria-label="Toggle menu">{open ? <X/> : <Menu/>}</button>
        </div>
        {open && <nav className="border-t border-[#e9eaf1] bg-white p-4 sm:hidden">{nav.map(({to,label}) => <NavLink key={to} to={to} onClick={() => setOpen(false)} className="block rounded-xl px-4 py-3 font-semibold">{label}</NavLink>)}<Link to="/conversation" onClick={() => setOpen(false)} className="mt-2 block rounded-xl bg-primary px-4 py-3 text-center font-bold text-white">New conversation</Link></nav>}
      </header>
      <main>{children}</main>
      <footer className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-8 text-center text-sm text-muted sm:flex-row sm:justify-between sm:px-8"><span>© 2026 Voxly. Conversations made clearer.</span><span>Privacy first · AI-ready architecture</span></footer>
    </div>
  )
}
