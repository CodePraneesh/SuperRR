import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { OverviewPage } from './pages/OverviewPage'
import { RankingsPage } from './pages/RankingsPage'
import { PlayerIntelligencePage } from './pages/PlayerIntelligencePage'
import { PlayerComparisonPage } from './pages/PlayerComparisonPage'
import { MatchupAnalysisPage } from './pages/MatchupAnalysisPage'
import { ScoutingAssistantPage } from './pages/ScoutingAssistantPage'
import { MethodologyPage } from './pages/MethodologyPage'

export const App: React.FC = () => {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {/* Page 1: Overview */}
        <Route path="/" element={<OverviewPage />} />

        {/* Page 2: Rankings */}
        <Route path="/rankings" element={<Navigate to="/rankings/ipl" replace />} />
        <Route path="/rankings/:scopeParam" element={<RankingsPage />} />

        {/* Page 3: Player Intelligence */}
        <Route
          path="/players"
          element={<Navigate to="/players/IPL/Batter/Rinku%20Singh" replace />}
        />
        <Route path="/players/:scope/:role/:name" element={<PlayerIntelligencePage />} />

        {/* Page 4: Player Comparison */}
        <Route path="/compare" element={<PlayerComparisonPage />} />

        {/* Page 5: Matchup Analysis */}
        <Route path="/matchup" element={<MatchupAnalysisPage />} />

        {/* Page 6: AI Scouting Assistant */}
        <Route path="/assistant" element={<ScoutingAssistantPage />} />

        {/* Page 7: Methodology */}
        <Route path="/methodology" element={<MethodologyPage />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
export default App
