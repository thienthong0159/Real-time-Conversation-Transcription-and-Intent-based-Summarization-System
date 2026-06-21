const mockTranscript = [
  { speaker: 'Sarah', timestamp: '00:03', text: 'Good morning! Shall we review the launch plan for the mobile app?' },
  { speaker: 'Minh', timestamp: '00:09', text: 'Absolutely. The design is ready, and the development team can begin on Monday.' },
  { speaker: 'Sarah', timestamp: '00:17', text: 'Great. Let’s prioritize onboarding and aim for a beta release next month.' },
]

/**
 * Mock speech-to-text adapter.
 * Replace this body with a streaming model/API (for example, WebSocket audio chunks)
 * while keeping the returned message shape stable for the UI.
 */
export async function transcribeAudio(audioBlob) {
  void audioBlob
  await delay(650)
  return mockTranscript.map(message => ({ ...message }))
}

export function getMockTranscriptChunk(index) {
  return mockTranscript[index] ? { ...mockTranscript[index] } : null
}

const delay = ms => new Promise(resolve => setTimeout(resolve, ms))
