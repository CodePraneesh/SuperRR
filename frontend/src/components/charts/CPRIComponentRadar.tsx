import React from 'react'
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { CPRIComponents } from '../../types/player'

interface CPRIComponentRadarProps {
  componentsA: CPRIComponents
  labelA?: string
  componentsB?: CPRIComponents
  labelB?: string
  height?: number
}

export const CPRIComponentRadar: React.FC<CPRIComponentRadarProps> = ({
  componentsA,
  labelA = 'Player A',
  componentsB,
  labelB = 'Player B',
  height = 280,
}) => {
  const data = [
    {
      subject: 'Pressure Impact (40%)',
      A: componentsA.pressure_impact,
      B: componentsB?.pressure_impact,
      fullMark: 100,
    },
    {
      subject: 'Adaptability (25%)',
      A: componentsA.pressure_adaptability,
      B: componentsB?.pressure_adaptability,
      fullMark: 100,
    },
    {
      subject: 'Consistency (20%)',
      A: componentsA.clutch_consistency,
      B: componentsB?.clutch_consistency,
      fullMark: 100,
    },
    {
      subject: 'Reliability (15%)',
      A: componentsA.reliability_confidence,
      B: componentsB?.reliability_confidence,
      fullMark: 100,
    },
  ]

  return (
    <div className="w-full h-full flex flex-col items-center justify-center">
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="#E5E7EB" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: '#101F43', fontSize: 11, fontWeight: 600 }}
          />
          <PolarRadiusAxis
            angle={45}
            domain={[0, 100]}
            tick={{ fill: '#94A3B8', fontSize: 10 }}
            stroke="#E5E7EB"
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
          />
          <Radar
            name={labelA}
            dataKey="A"
            stroke="#EC008C"
            fill="#EC008C"
            fillOpacity={0.15}
            strokeWidth={2}
          />
          {componentsB && (
            <Radar
              name={labelB}
              dataKey="B"
              stroke="#101F43"
              fill="#101F43"
              fillOpacity={0.1}
              strokeWidth={2}
            />
          )}
        </RadarChart>
      </ResponsiveContainer>
      {componentsB && (
        <div className="flex items-center gap-6 mt-2 text-xs font-semibold">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-[#EC008C]" />
            <span className="text-[#101F43]">{labelA}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-[#101F43]" />
            <span className="text-[#101F43]">{labelB}</span>
          </div>
        </div>
      )}
    </div>
  )
}
