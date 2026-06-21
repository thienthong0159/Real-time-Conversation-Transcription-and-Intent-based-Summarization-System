const translations = [
  'Chào buổi sáng! Chúng ta cùng xem lại kế hoạch ra mắt ứng dụng di động nhé?',
  'Chắc chắn rồi. Thiết kế đã sẵn sàng và đội phát triển có thể bắt đầu vào thứ Hai.',
  'Tuyệt vời. Hãy ưu tiên quy trình làm quen và hướng tới bản beta vào tháng tới.',
]

/**
 * Mock translation adapter. Replace with your translation model/API call.
 * The future integration can use `text`, source metadata, and `targetLanguage`.
 */
export async function translateText(text, targetLanguage, index = 0) {
  await new Promise(resolve => setTimeout(resolve, 320))
  if (targetLanguage === 'English') return text
  return translations[index] ?? `[${targetLanguage}] ${text}`
}
