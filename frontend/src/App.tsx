import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import PortfolioPage from './pages/PortfolioPage'
import SignalsPage from './pages/SignalsPage'
import RecommendationsPage from './pages/RecommendationsPage'
import JournalPage from './pages/JournalPage'
import BacktestPage from './pages/BacktestPage'
import WatchlistPage from './pages/WatchlistPage'
import NewsPage from './pages/NewsPage'
import AlertsPage from './pages/AlertsPage'
import RiskPage from './pages/RiskPage'
import LearningPage from './pages/LearningPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 25_000,
      refetchInterval: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard"       element={<Dashboard />} />
            <Route path="portfolio"       element={<PortfolioPage />} />
            <Route path="signals"         element={<SignalsPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="journal"         element={<JournalPage />} />
            <Route path="backtest"        element={<BacktestPage />} />
            <Route path="watchlist"       element={<WatchlistPage />} />
            <Route path="news"            element={<NewsPage />} />
            <Route path="alerts"          element={<AlertsPage />} />
            <Route path="risk"            element={<RiskPage />} />
            <Route path="learning"        element={<LearningPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
