import { ArrowLeft, Circle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { LanguageSelect } from '../components/common/LanguageSelect'
import { RecorderControls } from '../components/conversation/RecorderControls'
import { SummaryResult } from '../components/conversation/SummaryResult'
import { TranscriptPanel } from '../components/conversation/TranscriptPanel'
import { startRecording, pauseRecording, stopRecording } from '../modules/audio-recording/audioRecordingService'
import { getMockTranscriptChunk, transcribeAudio } from '../modules/speech-to-text/speechToTextService'
import { translateText } from '../modules/translation/translationService'
import { generateSummary } from '../modules/summarization/summarizationService'
import { analyzeIntent } from '../modules/intent-analysis/intentAnalysisService'
import { saveConversation } from '../modules/conversation-history/conversationHistoryService'

const sourceLanguages = ['Auto Detect', 'Vietnamese', 'English', 'Japanese', 'Korean', 'Chinese']
const targetLanguages = ['Vietnamese', 'English', 'Japanese', 'Korean', 'Chinese']

export function ConversationPage() {
  const [source, setSource] = useState('Auto Detect')
  const [target, setTarget] = useState('Vietnamese')
  const [status, setStatus] = useState('Idle')
  const [seconds, setSeconds] = useState(0)
  const [messages, setMessages] = useState([])
  const [translations, setTranslations] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const chunkTimer = useRef(null)
  const nextChunk = useRef(0)
  const conversationId = useRef(`conversation-${Date.now()}`)

  useEffect(() => { if (status !== 'Recording') return; const timer = setInterval(() => setSeconds(value => value + 1), 1000); return () => clearInterval(timer) }, [status])
  useEffect(() => () => clearInterval(chunkTimer.current), [])

  const appendNextChunk = async () => {
    const index = nextChunk.current
    const chunk = getMockTranscriptChunk(index)
    if (!chunk) return
    nextChunk.current += 1
    setMessages(current => [...current, chunk])
    const translated = await translateText(chunk.text, target, index)
    setTranslations(current => [...current, { ...chunk, speaker: `${chunk.speaker} · ${target}`, text: translated }])
  }

  const handleStart = async () => {
    await startRecording(); setStatus('Recording'); setSummary(null)
    await appendNextChunk()
    clearInterval(chunkTimer.current)
    chunkTimer.current = setInterval(appendNextChunk, 3300)
  }

  const handlePause = () => { pauseRecording(); setStatus('Paused'); clearInterval(chunkTimer.current) }

  const handleStop = async () => {
    clearInterval(chunkTimer.current)
    const blob = stopRecording()
    const completeTranscript = await transcribeAudio(blob)
    setMessages(completeTranscript)
    const translated = await Promise.all(completeTranscript.map(async (message, index) => ({ ...message, speaker: `${message.speaker} · ${target}`, text: await translateText(message.text, target, index) })))
    setTranslations(translated); setStatus('Completed')
    saveConversation({ id: conversationId.current, date: new Intl.DateTimeFormat('en', { month:'short', day:'numeric', year:'numeric' }).format(new Date()), time: new Intl.DateTimeFormat('en', { hour:'numeric', minute:'2-digit' }).format(new Date()), duration: formatTime(seconds), sourceLanguage: source === 'Auto Detect' ? 'English (detected)' : source, targetLanguage: target, summary: 'Summary not generated yet', transcript: completeTranscript, translations: translated, topics: [], intent: 'Pending analysis', keyPoints: [] })
  }

  const handleSummary = async () => {
    setLoading(true)
    const transcriptText = messages.map(message => message.text).join(' ')
    const [summaryResult, intentResult] = await Promise.all([generateSummary(transcriptText), analyzeIntent(transcriptText)])
    const result = { ...summaryResult, ...intentResult }
    setSummary(result); setLoading(false)
    saveConversation({ id: conversationId.current, date: new Intl.DateTimeFormat('en', { month:'short', day:'numeric', year:'numeric' }).format(new Date()), time: new Intl.DateTimeFormat('en', { hour:'numeric', minute:'2-digit' }).format(new Date()), duration: formatTime(seconds), sourceLanguage: source === 'Auto Detect' ? 'English (detected)' : source, targetLanguage: target, ...result, transcript: messages, translations })
  }

  return <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-12">
    <div className="mb-7 flex items-start gap-4"><Link to="/" className="mt-1 grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-muted shadow-sm transition hover:text-primary"><ArrowLeft size={19}/></Link><div><p className="eyebrow mb-1">Live workspace</p><h1 className="font-display text-2xl font-extrabold sm:text-3xl">Real-time conversation</h1></div></div>
    <section className="card mb-5 flex flex-col gap-4 p-4 sm:flex-row sm:items-end sm:p-5"><div className="flex flex-1 gap-3"><LanguageSelect label="Source language" value={source} onChange={setSource} options={sourceLanguages}/><LanguageSelect label="Target language" value={target} onChange={setTarget} options={targetLanguages}/></div><div className="sm:ml-auto"><span className="mb-1.5 block text-xs font-semibold text-muted">Recording status</span><span className={`flex h-[42px] items-center gap-2 rounded-xl px-4 text-sm font-bold ${status === 'Recording' ? 'bg-red-50 text-red-500' : status === 'Completed' ? 'bg-emerald-50 text-emerald-600' : 'bg-[#f2f3f7] text-muted'}`}><Circle size={9} fill="currentColor"/>{status}</span></div></section>
    <div className="grid gap-5 lg:grid-cols-2"><TranscriptPanel title="Original transcript" subtitle={source === 'Auto Detect' ? 'Language detected automatically' : source} messages={messages} emptyText="Your transcript will appear here as you speak"/><TranscriptPanel translated title="Translated text" subtitle={`Translated to ${target}`} messages={translations} emptyText="Translations will appear here in real time"/></div>
    <div className="mt-5"><RecorderControls status={status} elapsed={formatTime(seconds)} onStart={handleStart} onPause={handlePause} onStop={handleStop}/></div>
    {status === 'Completed' && <div className="mt-5"><SummaryResult summary={summary} loading={loading} onGenerate={handleSummary}/></div>}
  </div>
}

function formatTime(total) { const minutes = Math.floor(total / 60).toString().padStart(2,'0'); const seconds = (total % 60).toString().padStart(2,'0'); return `${minutes}:${seconds}` }
