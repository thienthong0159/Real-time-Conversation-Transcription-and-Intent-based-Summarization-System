import { Languages, MessageSquareText } from 'lucide-react'

export function TranscriptPanel({ title, subtitle, messages, translated = false, emptyText }) {
  const Icon = translated ? Languages : MessageSquareText
  return <section className="card flex min-h-[390px] flex-col overflow-hidden">
    <div className="flex items-center gap-3 border-b border-[#eff0f5] px-5 py-4 sm:px-6"><span className={`grid h-10 w-10 place-items-center rounded-xl ${translated ? 'bg-cyan/10 text-cyan' : 'bg-primary/10 text-primary'}`}><Icon size={19}/></span><div><h2 className="font-display font-bold">{title}</h2><p className="text-xs text-muted">{subtitle}</p></div></div>
    <div className="flex-1 space-y-4 p-5 sm:p-6">{messages.length ? messages.map((message, index) => <article key={`${message.timestamp}-${index}`} className={`max-w-[92%] rounded-2xl p-4 ${translated ? 'ml-auto rounded-tr-md bg-[#edfafd]' : 'rounded-tl-md bg-[#f1efff]'}`}><div className="mb-1.5 flex items-center justify-between gap-4"><span className={`text-xs font-bold ${translated ? 'text-[#168ca3]' : 'text-primary'}`}>{message.speaker}</span><time className="text-[11px] text-muted">{message.timestamp}</time></div><p className="text-[15px] leading-relaxed text-ink">{message.text}</p></article>) : <div className="grid h-full min-h-[260px] place-items-center text-center"><div><Icon className="mx-auto mb-3 text-[#c9cbd7]" size={32}/><p className="text-sm text-muted">{emptyText}</p></div></div>}</div>
  </section>
}
