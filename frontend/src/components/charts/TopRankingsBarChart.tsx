import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface TopRankingsBarChartProps {
  players: any[]
  onSelectPlayer?: (player: any) => void
  height?: number
}

export const TopRankingsBarChart: React.FC<TopRankingsBarChartProps> = ({
  players,
  onSelectPlayer,
  height = 320,
}) => {
  const top10 = [...players]
    .sort((a, b) => b.cpri_score - a.cpri_score)
    .slice(0, 10)
    .map((p, idx) => ({
      name: p.player_name,
      cpri: p.cpri_score,
      rank: p.official_rank || idx + 1,
      ci: p.rank_uncertainty?.ci_display || '',
      tier: p.confidence_tier || p.ranking_tier || 'Official Top 10',
      evidence: p.competition_evidence || p.competition_scope,
      raw: p,
    }))

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={top10}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 85, bottom: 5 }}
        >
          <XAxis
            type="number"
            domain={[60, 100]}
            tick={{ fill: '#64748B', fontSize: 11 }}
            stroke="#E5E7EB"
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: '#101F43', fontSize: 12, fontWeight: 600 }}
            stroke="#E5E7EB"
            width={120}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FFFFFF',
              borderColor: '#E5E7EB',
              borderRadius: '6px',
              fontSize: '12px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            }}
            formatter={(value: any, name: any, item: any) => [
              `${Number(value).toFixed(2)} CPRI ${item.payload.ci ? `(CI ${item.payload.ci})` : ''}`,
              `Rank #${item.payload.rank} • ${item.payload.tier}`,
            ]}
          />
          <Bar
            dataKey="cpri"
            radius={[0, 4, 4, 0]}
            onClick={(entry) => onSelectPlayer && onSelectPlayer(entry.raw)}
            cursor="pointer"
          >
            {top10.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={index === 0 ? '#EC008C' : index < 3 ? '#101F43' : '#334155'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
