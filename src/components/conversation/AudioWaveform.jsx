export function AudioWaveform({ active = false }) {
  const bars = [8,16,24,13,29,19,10,23,31,17,27,12,20,32,16,25,9,19,28,14,22,10,18,26]
  return <div className="flex h-12 items-center justify-center gap-1" aria-label={active ? 'Audio recording waveform' : 'Audio waveform idle'}>{bars.map((height, i) => <span key={i} className={`w-1 rounded-full ${active ? 'wave-bar bg-primary' : 'bg-[#d7d5ef]'}`} style={{ height, animationDelay: `${i * 55}ms` }}/>)}</div>
}
