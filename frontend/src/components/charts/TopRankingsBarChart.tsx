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
import type { PlayerSummaryItem } from '../../types/player'

interface TopRankingsBarChartProps {
  players: PlayerSummaryItem[]
  onSelectPlayer?: (player: PlayerSummaryItem) => void
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
      tier: p.ranking_tier,
      raw: p,
    }))

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={top10}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 75, bottom: 5 }}
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
            width={110}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FFFFFF',
              borderColor: '#E5E7EB',
              borderRadius: '6px',
              color: '#101F43',
              fontSize: '12px',
              boxShadow: '0 4px 6px -1px rgba(16, 31, 67, 0.08)',
            }}
            formatter={(value: any) => [`${Number(value).toFixed(2)} CPRI`, 'Score']}
            labelFormatter={(name: any, entry: any) => {
              const item = entry?.[0]?.payload
              return `#${item?.rank} ${name} (${item?.tier})`
            }}
          />
          <Bar
            dataKey="cpri"
            radius={[0, 4, 4, 0]}
            onClick={(data) => onSelectPlayer && onSelectPlayer(data.raw)}
            cursor={onSelectPlayer ? 'pointer' : 'default'}
          >
            {top10.map((entry, index) => {
              // Problem Statement Theme: #1 rank in Rajasthan Royals pink (#EC008C), others in deep navy (#101F43)
              const fill = index === 0 ? '#EC008C' : '#101F43'
              return <Cell key={`cell-${index}`} fill={fill} />
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
