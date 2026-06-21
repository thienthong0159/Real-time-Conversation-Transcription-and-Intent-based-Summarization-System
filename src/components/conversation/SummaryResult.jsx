import { BrainCircuit, CheckCircle2, Sparkles, Tags } from 'lucide-react'

export function SummaryResult({ summary, loading, onGenerate }) {
  if (!summary) return <section className="card flex flex-col items-center justify-between gap-5 p-6 text-center sm:flex-row sm:text-left"><div><p className="eyebrow mb-2">Conversation complete</p><h2 className="font-display text-xl font-bold">Turn this conversation into action</h2><p className="mt-1 text-sm text-muted">Generate a concise recap, topics, intent, and key points.</p></div><button onClick={onGenerate} disabled={loading} className="btn-primary shrink-0"><Sparkles size={18}/>{loading ? 'Generating…' : 'Generate summary'}</button></section>
  return <section className="card overflow-hidden"><div className="bg-gradient-to-r from-primary to-[#8175f1] p-6 text-white sm:p-8"><div className="mb-3 flex items-center gap-2 text-sm font-bold text-white/80"><Sparkles size={17}/>AI conversation insight</div><h2 className="font-display text-2xl font-bold">Conversation summary</h2><p className="mt-3 max-w-4xl leading-relaxed text-white/90">{summary.summary}</p></div><div className="grid gap-0 divide-y divide-[#ececf3] md:grid-cols-3 md:divide-x md:divide-y-0">
    <SummaryCell icon={Tags} title="Main topics"><div className="flex flex-wrap gap-2">{summary.topics.map(topic => <span key={topic} className="rounded-full bg-primary/8 px-3 py-1 text-xs font-bold text-primary">{topic}</span>)}</div></SummaryCell>
    <SummaryCell icon={BrainCircuit} title="Detected intent"><p className="text-sm leading-relaxed text-muted">{summary.intent}</p></SummaryCell>
    <SummaryCell icon={CheckCircle2} title="Key points"><ul className="space-y-2">{summary.keyPoints.map(point => <li key={point} className="flex gap-2 text-sm text-muted"><CheckCircle2 size={16} className="mt-0.5 shrink-0 text-cyan"/>{point}</li>)}</ul></SummaryCell>
  </div></section>
}

function SummaryCell({icon: Icon, title, children}) { return <div className="p-6"><div className="mb-4 flex items-center gap-2 font-display font-bold"><Icon size={19} className="text-primary"/>{title}</div>{children}</div> }
