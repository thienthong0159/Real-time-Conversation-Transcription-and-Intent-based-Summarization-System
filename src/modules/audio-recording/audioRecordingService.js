let mockStream = null

/**
 * Mock recorder adapter. Replace with MediaRecorder and microphone stream setup.
 * A real implementation should return a recording session and emit audio chunks.
 */
export async function startRecording() {
  mockStream = { startedAt: Date.now(), state: 'recording' }
  return { ...mockStream }
}

export function pauseRecording() {
  if (mockStream) mockStream.state = 'paused'
  return mockStream ? { ...mockStream } : null
}

/** Replace the mock Blob with the actual MediaRecorder output later. */
export function stopRecording() {
  const audioBlob = new Blob(['mock-audio-data'], { type: 'audio/webm' })
  mockStream = null
  return audioBlob
}
