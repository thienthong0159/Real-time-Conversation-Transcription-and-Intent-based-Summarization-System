/**
 * Future API orchestration boundary. Use this module for authenticated HTTP calls,
 * request retries, and mapping backend responses into the app's domain shapes.
 * It intentionally contains no network calls while the project is UI-only.
 */
export async function checkApiHealth() {
  return { status: 'mock', connected: false }
}
