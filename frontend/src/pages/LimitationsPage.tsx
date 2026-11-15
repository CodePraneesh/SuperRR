import React from 'react'
import {
  AlertTriangle,
  ShieldAlert,
  BarChart2,
  Info,
  Scale,
  CheckCircle2,
  HelpCircle,
  TrendingDown,
  Layers
} from 'lucide-react'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'

export const LimitationsPage: React.FC = () => {
  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="bg-[#101F43] border border-[#EC008C]/40 rounded-2xl p-6 md:p-8 text-white relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider bg-[#EC008C] text-white px-2.5 py-0.5 rounded font-black">
              Scientific Rigor & Transparency
            </span>
            <span className="text-xs text-slate-300 font-mono">
              CPRI v1.0.0 Uncertainty Audit
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-3">
            Limitations, Sample Uncertainty & Methodology Audits
          </h1>
          <p className="text-sm md:text-base text-slate-300 leading-relaxed">
            In competitive cricket analytics, honest evaluation of measurement noise and sample constraints is as critical as point estimates. This page documents the statistical boundaries, 90% bootstrap rank confidence intervals, and two-tier classification system of SupeRR Intelligence.
          </p>
        </div>
      </div>

      {/* Two-Tier System Explanation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card variant="default" className="border-emerald-500/30 bg-emerald-950/10 p-6">
          <div className="flex items-start gap-3 mb-3">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-600 font-bold">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-[#101F43]">High Confidence Tier</h3>
                <Badge variant="high" size="sm">Stable Rank</Badge>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Substantial pressure delivery exposure (&ge;300 balls), high reliability score (&ge;75.0), and bounded bootstrap rank CI (&le;65 rank span).
              </p>
            </div>
          </div>
          <div className="text-xs text-slate-600 space-y-1.5 pt-2 border-t border-emerald-500/20">
            <p><strong>Primary Candidates:</strong> Suryakumar Yadav [2, 25], Rinku Singh [1, 51], Mitchell Santner [2, 36], Rashid Khan [2, 33], Matheesha Pathirana [4, 49], Jasprit Bumrah [3, 67].</p>
            <p className="text-slate-500">Sufficient match sample size ensures ranking position reflects persistent clutch skill rather than sample variance.</p>
          </div>
        </Card>

        <Card variant="default" className="border-amber-500/30 bg-amber-950/10 p-6">
          <div className="flex items-start gap-3 mb-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-600 font-bold">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-[#101F43]">Exploratory Tier</h3>
                <Badge variant="medium" size="sm">High Uncertainty</Badge>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Elite per-delivery rate stats but constrained total pressure volume (&lt;250 deliveries) leading to wide bootstrap rank intervals (&gt;65 rank span).
              </p>
            </div>
          </div>
          <div className="text-xs text-slate-600 space-y-1.5 pt-2 border-t border-amber-500/20">
            <p><strong>Notable Examples:</strong> Matthew Wade [1, 22] (191 balls), Sufiyan Muqeem [1, 74] (151 balls), Jamie Overton [1, 71] (168 balls).</p>
            <p className="text-slate-500">Point estimates are empirically verified, but rank uncertainty indicates true skill could plausibly range across the mid-table under resampling.</p>
          </div>
        </Card>
      </div>

      {/* Case Study: Wide CIs Audit */}
      <Card variant="default" className="p-6 border-[#101F43]/20">
        <div className="flex items-center gap-2 mb-4">
          <ShieldAlert className="w-5 h-5 text-[#EC008C]" />
          <h2 className="text-lg font-bold text-[#101F43]">
            Deep-Dive: Sample Size Impact on Top-Ranked Outliers
          </h2>
        </div>
        <p className="text-xs text-slate-600 mb-4 leading-relaxed">
          The table below demonstrates why point ranks alone must never be used in professional scouting without bootstrap uncertainty intervals:
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border border-slate-200 rounded-lg">
            <thead className="bg-[#101F43] text-white">
              <tr>
                <th className="py-2.5 px-3">Player</th>
                <th className="py-2.5 px-3">Official Rank</th>
                <th className="py-2.5 px-3">90% Bootstrap CI</th>
                <th className="py-2.5 px-3">CI Width</th>
                <th className="py-2.5 px-3">Pressure Deliveries</th>
                <th className="py-2.5 px-3">Tier</th>
                <th className="py-2.5 px-3">Scouting Interpretation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              <tr className="hover:bg-slate-50">
                <td className="py-2.5 px-3 font-bold text-[#101F43]">Matthew Wade</td>
                <td className="py-2.5 px-3 font-mono font-bold text-[#EC008C]">#1 (Batter)</td>
                <td className="py-2.5 px-3 font-mono font-bold text-amber-600">[1, 22]</td>
                <td className="py-2.5 px-3 font-mono">21 ranks</td>
                <td className="py-2.5 px-3 font-mono">191 balls</td>
                <td className="py-2.5 px-3"><Badge variant="medium" size="sm">Exploratory</Badge></td>
                <td className="py-2.5 px-3 text-slate-600">Spectacular finishing efficiency (SR 178+ in high leverage), but 90% CI spans outside Top 20.</td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="py-2.5 px-3 font-bold text-[#101F43]">Sufiyan Muqeem</td>
                <td className="py-2.5 px-3 font-mono font-bold text-[#EC008C]">#2 (Bowler)</td>
                <td className="py-2.5 px-3 font-mono font-bold text-amber-600">[1, 74]</td>
                <td className="py-2.5 px-3 font-mono text-red-600 font-bold">73 ranks</td>
                <td className="py-2.5 px-3 font-mono">151 balls</td>
                <td className="py-2.5 px-3"><Badge variant="medium" size="sm">Exploratory</Badge></td>
                <td className="py-2.5 px-3 text-slate-600">Elite left-arm wrist spin dot% in T20Is, but CI extends to #74 due to modest 151-ball sample.</td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="py-2.5 px-3 font-bold text-[#101F43]">Jamie Overton</td>
                <td className="py-2.5 px-3 font-mono font-bold text-[#EC008C]">#4 (Bowler)</td>
                <td className="py-2.5 px-3 font-mono font-bold text-amber-600">[1, 71]</td>
                <td className="py-2.5 px-3 font-mono text-red-600 font-bold">70 ranks</td>
                <td className="py-2.5 px-3 font-mono">168 balls</td>
                <td className="py-2.5 px-3"><Badge variant="medium" size="sm">Exploratory</Badge></td>
                <td className="py-2.5 px-3 text-slate-600">High-impact strike bowler in short bursts; high variance across resampled matches.</td>
              </tr>
              <tr className="hover:bg-slate-50 bg-emerald-50/50">
                <td className="py-2.5 px-3 font-bold text-[#101F43]">Mitchell Santner</td>
                <td className="py-2.5 px-3 font-mono font-bold text-[#EC008C]">#1 (Bowler)</td>
                <td className="py-2.5 px-3 font-mono font-bold text-emerald-600">[2, 36]</td>
                <td className="py-2.5 px-3 font-mono">34 ranks</td>
                <td className="py-2.5 px-3 font-mono">653 balls</td>
                <td className="py-2.5 px-3"><Badge variant="high" size="sm">High Confidence</Badge></td>
                <td className="py-2.5 px-3 text-slate-600">Large volume dual-format spine with peerless middle/death economy restraint.</td>
              </tr>
              <tr className="hover:bg-slate-50 bg-emerald-50/50">
                <td className="py-2.5 px-3 font-bold text-[#101F43]">Rinku Singh</td>
                <td className="py-2.5 px-3 font-mono font-bold text-[#EC008C]">#5 (Batter)</td>
                <td className="py-2.5 px-3 font-mono font-bold text-emerald-600">[1, 51]</td>
                <td className="py-2.5 px-3 font-mono">50 ranks</td>
                <td className="py-2.5 px-3 font-mono">457 balls</td>
                <td className="py-2.5 px-3"><Badge variant="high" size="sm">High Confidence</Badge></td>
                <td className="py-2.5 px-3 text-slate-600">Proven multi-season match finisher; ranks #1 in isolated IPL pressure cohorts.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      {/* Adaptability Formulation & Sensitivity */}
      <Card variant="default" className="p-6 border-[#101F43]/20">
        <div className="flex items-center gap-2 mb-3">
          <Scale className="w-5 h-5 text-[#EC008C]" />
          <h2 className="text-lg font-bold text-[#101F43]">
            Phase 8 Adaptability Formula & Weight Sensitivity
          </h2>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed mb-4">
          In Phase 8, the Pressure Adaptability (PA) component formula was frozen as:
        </p>
        <div className="p-4 bg-slate-900 text-pink-300 font-mono text-sm rounded-xl mb-4 border border-pink-500/20">
          <code>PA = 0.60 * Pressure_Impact + 0.40 * max(Delta_to_Baseline, -5.0)</code>
        </div>
        <div className="text-xs text-slate-600 space-y-2 mb-4 leading-relaxed">
          <p>
            <strong>Mathematical Consequence:</strong> Because PA includes a 60% term of Pressure Impact itself, the effective weight on raw pressure impact within the master CPRI formula is:
            <span className="font-mono font-bold text-[#101F43] ml-1">40% (Direct PI) + 25% * 60% (Indirect PI) = 55% Total Effective Impact Weight</span>.
          </p>
          <p>
            This design intentionally prioritizes absolute pressure performance over relative differential, preventing low-performing baseline players from gaining artificial boosts through modest positive deltas.
          </p>
        </div>

        <div className="border-t border-slate-200 pt-4">
          <h4 className="text-xs font-bold text-[#101F43] uppercase tracking-wider mb-2">
            Weight Sensitivity Analysis (&plusmn;5 Point Variations)
          </h4>
          <p className="text-xs text-slate-500 mb-3">
            Testing variations in CPRI component weights (Baseline: 40% PI / 25% PA / 20% CC / 15% RC):
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <div className="font-bold text-[#101F43] mb-1">Impact-Heavy (45/20/20/15)</div>
              <p className="text-slate-600">Increases Wade and David lead; Top 5 batters remain completely invariant in composition with &plusmn;0.8 CPRI score movement.</p>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <div className="font-bold text-[#101F43] mb-1">Consistency-Heavy (35/20/30/15)</div>
              <p className="text-slate-600">Boosts high-volume anchors (Suryakumar, Santner, Bumrah); Santner expands lead at #1 bowler to +2.4 CPRI.</p>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <div className="font-bold text-[#101F43] mb-1">Delta-Only Adaptability</div>
              <p className="text-slate-600">Using purely delta without PI weighting increases noise among low-sample finishers but leaves 8 of Top 10 intact.</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Honest Boundary Declarations */}
      <Card variant="default" className="p-6 border-[#101F43]/20 bg-slate-50/50">
        <div className="flex items-center gap-2 mb-3">
          <Layers className="w-5 h-5 text-[#101F43]" />
          <h2 className="text-lg font-bold text-[#101F43]">
            Structural Data & Dataset Boundary Declarations
          </h2>
        </div>
        <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-[#EC008C] flex-shrink-0 mt-0.5" />
            <p>
              <strong>Chronological Boundary:</strong> Validation/test split uses strict temporal cutoff (Feb 1, 2026). Match-level outcomes never bleed across partitions.
            </p>
          </div>
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-[#EC008C] flex-shrink-0 mt-0.5" />
            <p>
              <strong>Format Conditioning:</strong> Expected performance adjustments are conditioned on format-level delivery baselines. They represent delivery-level expected adjustments rather than claiming perfect cross-format equivalence.
            </p>
          </div>
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-[#EC008C] flex-shrink-0 mt-0.5" />
            <p>
              <strong>Zero External Hallucination:</strong> All evaluations rely strictly on ball-by-ball variables present in the official data pack. No pitch, weather, player fitness, or speculative external metrics are synthesized.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
export default LimitationsPage
