import { CirclePause, Mic, Square } from 'lucide-react'
import { AudioWaveform } from './AudioWaveform'

export function RecorderControls({ status, elapsed, onStart, onPause, onStop }) {
  const active = status === 'Recording'
  return <section className="card relative overflow-hidden p-5 sm:p-6"><div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-primary to-cyan"/><div className="flex flex-col items-center gap-5 lg:flex-row">
    <div className="flex items-center gap-4 lg:w-52"><span className="relative grid h-12 w-12 place-items-center rounded-full bg-primary/10 text-primary">{active && <span className="pulse-ring absolute inset-0 rounded-full bg-primary/25"/>}<Mic size={21}/></span><div><p className="text-xs font-semibold text-muted">Recording time</p><p className="font-display text-2xl font-bold tabular-nums">{elapsed}</p></div></div>
    <div className="min-w-0 flex-1"><AudioWaveform active={active}/></div>
    <div className="flex w-full flex-wrap justify-center gap-2 lg:w-auto">
      <button onClick={onStart} disabled={active || status === 'Completed'} className="btn-primary flex-1 px-4 py-3 disabled:cursor-not-allowed disabled:opacity-40 sm:flex-none"><Mic size={18}/>{status === 'Paused' ? 'Resume' : 'Start recording'}</button>
      <button onClick={onPause} disabled={!active} className="btn-secondary flex-1 px-4 py-3 disabled:cursor-not-allowed disabled:opacity-40 sm:flex-none"><CirclePause size={18}/>Pause</button>
      <button onClick={onStop} disabled={!['Recording','Paused'].includes(status)} className="btn-secondary flex-1 border-red-100 px-4 py-3 text-red-500 disabled:cursor-not-allowed disabled:opacity-40 sm:flex-none"><Square size={17} fill="currentColor"/>Stop & save</button>
    </div>
  </div></section>
}
