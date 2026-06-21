import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { ConversationPage } from './pages/ConversationPage'
import { HistoryPage } from './pages/HistoryPage'
import { ConversationDetailPage } from './pages/ConversationDetailPage'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/conversation" element={<ConversationPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/history/:id" element={<ConversationDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}
