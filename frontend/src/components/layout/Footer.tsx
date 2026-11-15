import React from 'react'

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-[#E5E7EB] bg-white py-6 px-6 lg:px-8 text-xs text-slate-500">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-2">
          <span className="font-extrabold text-[#101F43]">
            Supe<span className="text-[#EC008C]">RR</span> Selector
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-slate-600">
            Season 2 Cricket Analytics • <strong className="text-[#101F43]">Measuring Pressure.</strong>
          </span>
        </div>

        <div className="flex items-center gap-4 text-[11px] font-mono text-slate-500">
          <span>Methodology: CPRI-v1.0.0-PROD-FREEZE</span>
          <span className="text-slate-300">•</span>
          <span className="text-[#101F43] font-semibold">Official Competition Specification</span>
        </div>
      </div>
    </footer>
  )
}
