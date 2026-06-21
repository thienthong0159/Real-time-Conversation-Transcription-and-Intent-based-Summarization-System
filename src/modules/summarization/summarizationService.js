/**
 * Mock summarization adapter. Replace this body with an LLM or summarization API.
 * Preserve the structured response so presentation components remain unchanged.
 */
export async function generateSummary(transcript) {
  void transcript
  await new Promise(resolve => setTimeout(resolve, 900))
  return {
    summary: 'The team aligned on launching the mobile app. Design is complete, development begins Monday, and the first milestone is a focused onboarding experience followed by a beta release next month.',
    keyPoints: ['Design handoff is complete', 'Development begins Monday', 'Beta release targeted for next month'],
  }
}
