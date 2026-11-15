import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import type { ContextualSplitsResponse } from '../../types/player'

interface PhaseSplitsBarChartProps {
  splits: ContextualSplitsResponse
  height?: number
}

export const PhaseSplitsBarChart: React.FC<PhaseSplitsBarChartProps> = ({
  splits,
  height = 260,
}) => {
  const isBatter = splits.role === 'Batter'
  const phases = splits.innings_phase_splits

  const pp = phases.powerplay || {}
  const mid = phases.middle || {}
  const dth = phases.death || {}

  const data = [
    {
      phase: 'Powerplay (1-6)',
      Rate: isBatter ? pp.strike_rate || 0 : pp.economy_rate || 0,
      Balls: isBatter ? pp.balls_faced || 0 : pp.balls_bowled || 0,
      Dots: pp.dot_percentage || 0,
    },
    {
      phase: 'Middle (7-16)',
      Rate: isBatter ? mid.strike_rate || 0 : mid.economy_rate || 0,
      Balls: isBatter ? mid.balls_faced || 0 : mid.balls_bowled || 0,
      Dots: mid.dot_percentage || 0,
    },
    {
      phase: 'Death (17-20)',
      Rate: isBatter ? dth.strike_rate || 0 : dth.economy_rate || 0,
      Balls: isBatter ? dth.balls_faced || 0 : dth.balls_bowled || 0,
      Dots: dth.dot_percentage || 0,
    },
  ]

  const rateLabel = isBatter ? 'Strike Rate' : 'Economy Rate'

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
          <XAxis dataKey="phase" tick={{ fill: '#64748B', fontSize: 11 }} stroke="#E5E7EB" />
          <YAxis tick={{ fill: '#64748B', fontSize: 11 }} stroke="#E5E7EB" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FFFFFF',
              borderColor: '#E5E7EB',
              borderRadius: '6px',
              color: '#101F43',
              fontSize: '12px',
              boxShadow: '0 4px 6px -1px rgba(16, 31, 67, 0.08)',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
          <Bar
            name={rateLabel}
            dataKey="Rate"
            fill={isBatter ? '#EC008C' : '#101F43'}
            radius={[3, 3, 0, 0]}
          />
          <Bar
            name="Dot Ball %"
            dataKey="Dots"
            fill="#94A3B8"
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
