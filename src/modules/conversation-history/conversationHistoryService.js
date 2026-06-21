const STORAGE_KEY = 'voxly-conversation-history'

export const seedHistory = [
  { id: 'demo-1', date: 'Jun 18, 2026', time: '10:24 AM', duration: '18:42', sourceLanguage: 'English', targetLanguage: 'Vietnamese', summary: 'Product team aligned on the mobile app launch, milestones, and ownership.', topics: ['Product launch', 'Mobile app'], intent: 'Planning', keyPoints: ['Finalize onboarding flow', 'Begin development Monday'] },
  { id: 'demo-2', date: 'Jun 15, 2026', time: '2:10 PM', duration: '32:08', sourceLanguage: 'Japanese', targetLanguage: 'English', summary: 'Client discovery call covering workflow requirements and delivery timelines.', topics: ['Client needs', 'Timeline'], intent: 'Requirements gathering', keyPoints: ['Share proposal this week', 'Confirm project scope'] },
  { id: 'demo-3', date: 'Jun 11, 2026', time: '9:05 AM', duration: '12:36', sourceLanguage: 'Korean', targetLanguage: 'English', summary: 'Weekly stand-up focused on progress, blockers, and the next sprint.', topics: ['Sprint', 'Blockers'], intent: 'Team update', keyPoints: ['Resolve authentication blocker', 'Prepare sprint demo'] },
]

/** Local mock repository. Replace these functions with API service calls later. */
export function getConversations() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || seedHistory } catch { return seedHistory }
}

export function getConversation(id) { return getConversations().find(item => item.id === id) }

export function saveConversation(conversation) {
  const next = [conversation, ...getConversations().filter(item => item.id !== conversation.id)]
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  return conversation
}
