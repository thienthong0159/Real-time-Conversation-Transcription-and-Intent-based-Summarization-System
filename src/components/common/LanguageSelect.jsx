import { ChevronDown } from 'lucide-react'

export function LanguageSelect({ label, value, onChange, options }) {
  return <label className="min-w-0 flex-1"><span className="mb-1.5 block text-xs font-semibold text-muted">{label}</span><span className="relative block"><select value={value} onChange={e => onChange(e.target.value)} className="w-full appearance-none rounded-xl border border-[#e5e6ee] bg-white py-2.5 pl-3 pr-9 text-sm font-semibold outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10">{options.map(option => <option key={option}>{option}</option>)}</select><ChevronDown size={16} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted"/></span></label>
}
