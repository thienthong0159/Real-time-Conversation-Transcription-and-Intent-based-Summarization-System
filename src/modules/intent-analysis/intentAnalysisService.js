/**
 * Mock intent analysis adapter. Replace with an intent classifier or LLM call.
 * Confidence scores or entities can be added here later without coupling the UI.
 */
export async function analyzeIntent(transcript) {
  void transcript
  await new Promise(resolve => setTimeout(resolve, 500))
  return {
    intent: 'Project planning and alignment',
    topics: ['Mobile app', 'Product launch', 'Onboarding', 'Beta release'],
  }
}
