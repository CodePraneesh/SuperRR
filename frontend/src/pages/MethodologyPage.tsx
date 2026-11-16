import React from 'react'
import {
  BookOpen,
  ShieldCheck,
  CheckCircle2,
  Lock,
  Layers,
  Activity,
  Flame,
  Award,
  AlertTriangle,
  Crown,
  FileText,
  Download,
  ExternalLink,
} from 'lucide-react'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'

export const MethodologyPage: React.FC = () => {
  const componentWeights = [
    {
      name: 'Pressure Impact',
      weight: '40%',
      badgeVariant: 'pink',
      desc: 'Evaluates direct expected run and dismissal residual contributions specifically on high-pressure deliveries (Pressure Index ≥ 50.0). Quantifies added output above baseline match expectations.',
    },
    {
      name: 'Pressure Adaptability',
      weight: '25%',
      badgeVariant: 'blue',
      desc: 'Measures player performance stability and acceleration across shifting pressure states. Contrasts high-pressure execution against low-pressure baseline rates to detect positive clutch scaling.',
    },
    {
      name: 'Clutch Consistency',
      weight: '20%',
      badgeVariant: 'official',
      desc: 'Assesses match-to-match variance and positive pressure match contribution ratio. Penalizes feast-or-famine execution and rewards dependable repeated delivery in high-stakes fixtures.',
    },
    {
      name: 'Reliability Confidence',
      weight: '15%',
      badgeVariant: 'gold',
      desc: 'Applies empirical Bayes shrinkage based on pressure ball sample depth (≥100 balls) and match dispersion (≥8 matches). Shrinks exploratory samples toward cohort baselines.',
    },
  ]

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-mono font-medium text-[#EC008C] mb-1">
          <Crown className="w-4 h-4 text-amber-500" />
          <span>Statistical Architecture & Franchise Standards</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-[#0F172A] flex items-center gap-2">
          <span>CPRI v1.0.0</span>
          <span className="text-pink-600 font-black">Methodology Specification</span>
        </h1>
        <p className="text-sm text-[#475569] mt-1">
          Formal mathematical documentation of the Clutch Performance Rating Index sealed under the Phase 3.5 Freeze.
        </p>
      </div>

      {/* Freeze Certification Banner */}
      <Card variant="royal" className="p-6 border-amber-300">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 shadow-xs">
              <Lock className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-bold text-[#0F172A]">Methodology Freeze Approved</span>
                <Badge variant="gold" size="sm">
                  CPRI-v1.0.0-PROD-FREEZE
                </Badge>
              </div>
              <p className="text-xs text-[#475569]">
                All weights, sigmoid parameters, pressure thresholds, and Bayesian priors are sealed and audited across 176 automated validation tests.
              </p>
            </div>
          </div>
          <div className="text-right text-xs font-mono text-[#64748B]">
            <div>Verification: <span className="text-[#0F172A] font-bold">100% Pass Rate</span></div>
            <div className="text-amber-800 font-bold">Zero Statistical Leakage</div>
          </div>
        </div>
      </Card>

      {/* Official 16-Page Submission Methodology Report & Required Report Sections */}
      <Card variant="default" className="p-6 border-pink-200 bg-pink-50/40 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-pink-200/60">
          <div className="flex items-start gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-pink-100 border border-pink-200 flex items-center justify-center text-[#EC008C] shrink-0 mt-0.5">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-[#0F172A]">
                  Official Methodology Report PDF (16 Pages)
                </h2>
                <span className="text-[10px] font-mono font-bold bg-[#EC008C] text-white px-2 py-0.5 rounded">
                  AUTHORITATIVE
                </span>
              </div>
              <p className="text-xs text-[#475569] mt-1 max-w-2xl leading-relaxed">
                Complete competition submission report documenting the mathematical formalization of CPRI, data pipelines, empirical validation, 90% bootstrap rank confidence intervals, and the official Top 10 lists.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <a
              href="/docs/SupeRR_Intelligence_Methodology_Report.pdf"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="View Methodology Report PDF in new browser tab"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-[#0F172A] text-xs font-bold transition-all border border-slate-300 focus:outline-none focus:ring-2 focus:ring-[#EC008C]"
            >
              <ExternalLink className="w-3.5 h-3.5 text-pink-600" />
              <span>View PDF</span>
            </a>
            <a
              href="/api/v1/official/report-pdf"
              download="SupeRR_Intelligence_Methodology_Report.pdf"
              aria-label="Download Official Methodology Report PDF"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#EC008C] hover:bg-[#d6007f] text-white text-xs font-bold transition-all shadow-md shadow-[#EC008C]/20 focus:outline-none focus:ring-2 focus:ring-[#EC008C]"
            >
              <Download className="w-3.5 h-3.5 text-white" />
              <span>Download PDF</span>
            </a>
          </div>
        </div>

        {/* Five Required Report Sections */}
        <div className="mt-5 space-y-3">
          <div className="text-xs uppercase font-mono tracking-wider text-[#EC008C] font-bold flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-[#EC008C]" />
            <span>The Five Required Report Sections</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-1">
            {/* Section 1 */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 flex flex-col justify-between shadow-xs">
              <div>
                <div className="text-[10px] font-mono text-[#EC008C] font-bold mb-1">SECTION 1</div>
                <h4 className="text-xs font-bold text-[#0F172A] mb-1.5">Pressure Definition</h4>
                <p className="text-[11px] text-[#475569] leading-relaxed">
                  Meaning, indicators, and separation of high vs low pressure. Pre-ball leverage (PI ≥ 50.0) with zero lookahead bias.
                </p>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 text-[10px] font-mono text-[#64748B]">
                PDF Pages 1–3
              </div>
            </div>

            {/* Section 2 */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 flex flex-col justify-between shadow-xs">
              <div>
                <div className="text-[10px] font-mono text-blue-700 font-bold mb-1">SECTION 2</div>
                <h4 className="text-xs font-bold text-[#0F172A] mb-1.5">Performance Measurement</h4>
                <p className="text-[11px] text-[#475569] leading-relaxed">
                  Metrics, baselines, and rating logic. LightGBM expected residuals and ball-by-ball WPA delta attribution.
                </p>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 text-[10px] font-mono text-[#64748B]">
                PDF Pages 4–6
              </div>
            </div>

            {/* Section 3 */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 flex flex-col justify-between shadow-xs">
              <div>
                <div className="text-[10px] font-mono text-emerald-700 font-bold mb-1">SECTION 3</div>
                <h4 className="text-xs font-bold text-[#0F172A] mb-1.5">Fair Comparisons</h4>
                <p className="text-[11px] text-[#475569] leading-relaxed">
                  Sample sizes, eligibility thresholds, context normalization, empirical Bayes shrinkage, and format evidence tiers.
                </p>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 text-[10px] font-mono text-[#64748B]">
                PDF Pages 7–9
              </div>
            </div>

            {/* Section 4 */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 flex flex-col justify-between shadow-xs">
              <div>
                <div className="text-[10px] font-mono text-amber-700 font-bold mb-1">SECTION 4</div>
                <h4 className="text-xs font-bold text-[#0F172A] mb-1.5">Evidence for Official Top 10</h4>
                <p className="text-[11px] text-[#475569] leading-relaxed">
                  Deep-dive dossiers for official Top 10 Batters and Bowlers. Tactical profiling, phase splits, and empirical evidence.
                </p>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 text-[10px] font-mono text-[#64748B]">
                PDF Pages 10–13
              </div>
            </div>

            {/* Section 5 */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 flex flex-col justify-between shadow-xs">
              <div>
                <div className="text-[10px] font-mono text-purple-700 font-bold mb-1">SECTION 5</div>
                <h4 className="text-xs font-bold text-[#0F172A] mb-1.5">Reliability & Limitations</h4>
                <p className="text-[11px] text-[#475569] leading-relaxed">
                  500-iteration bootstrap rank CIs, sample cutoff sensitivity (8/10/12 matches), data windows, and model boundaries.
                </p>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 text-[10px] font-mono text-[#64748B]">
                PDF Pages 14–16
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* 4 Component Pillars Grid */}
      <div>
        <h2 className="text-base font-bold text-[#0F172A] mb-4 flex items-center gap-2">
          <Layers className="w-5 h-5 text-pink-600" />
          The Four Weighted Components
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {componentWeights.map((comp) => (
            <Card key={comp.name} variant="default" className="p-5 border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-bold text-[#0F172A]">{comp.name}</h3>
                <span className="text-sm font-black font-mono px-2.5 py-0.5 rounded bg-pink-50 text-[#EC008C] border border-pink-200">
                  {comp.weight} Weight
                </span>
              </div>
              <p className="text-xs text-[#475569] leading-relaxed">{comp.desc}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Deep Dives Section */}
      <div className="space-y-6">
        <h2 className="text-base font-bold text-[#0F172A] flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          Core Mathematical Foundations
        </h2>

        {/* 1. Pressure Index Quantification */}
        <Card variant="subtle" className="p-6 space-y-3 border-slate-200">
          <div className="flex items-center gap-2 text-[#EC008C] font-bold text-sm">
            <Flame className="w-4 h-4 text-[#EC008C]" />
            1. Pre-Ball Pressure Index Quantification (PI ≥ 50.0)
          </div>
          <p className="text-xs text-[#475569] leading-relaxed">
            The Pressure Index (PI) is calculated prior to the release of every delivery. It synthesizes pre-ball required run rate (chasing), current run rate vs par score (1st innings), remaining wickets in hand, and overs remaining using non-linear sigmoid leverage curves. Zero lookahead leakage is permitted: the pressure calculation on ball <em>n</em> depends strictly on the match state up to ball <em>n-1</em>.
          </p>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 font-mono text-xs text-[#EC008C] font-semibold">
            High-Pressure Delivery Definition: PI(match_state) ≥ 50.0 on [0, 100] scale
          </div>
        </Card>

        {/* 2. Expected Performance Residuals */}
        <Card variant="subtle" className="p-6 space-y-3 border-slate-200">
          <div className="flex items-center gap-2 text-blue-700 font-bold text-sm">
            <CheckCircle2 className="w-4 h-4 text-blue-700" />
            2. Expected Residual Modeling (LightGBM Baselines)
          </div>
          <p className="text-xs text-[#475569] leading-relaxed">
            Standard statistics fail because a dot ball in over 2 is vastly different from a dot ball in over 19. Using LightGBM gradient-boosted trees trained on 200,000+ historical legal deliveries, the system computes pre-delivery expected runs and expected dismissal probabilities. A player’s raw contribution is the residual between their actual outcome and the baseline expected outcome under identical match conditions.
          </p>
        </Card>

        {/* 3. Win Probability Added Attribution */}
        <Card variant="subtle" className="p-6 space-y-3 border-slate-200">
          <div className="flex items-center gap-2 text-[#EC008C] font-bold text-sm">
            <Award className="w-4 h-4 text-[#EC008C]" />
            3. Win Probability Added (WPA) Credit Assignment
          </div>
          <p className="text-xs text-[#475569] leading-relaxed">
            Every ball alters the batting team’s probability of victory: <code className="bg-slate-100 text-[#EC008C] px-1.5 py-0.5 rounded border border-slate-200 font-semibold">ΔWPA = P_win(t) - P_win(t-1)</code>. Pure extras (byes, leg-byes) and ambiguous events are isolated to unattributed buckets. Bowler-credited dismissals (bowled, caught, lbw, stumped, hit wicket) award positive WPA to the bowler, while run outs and penalties are partitioned strictly to avoid misattribution.
          </p>
        </Card>

        {/* 4. Bayesian Reliability & Confidence Classification */}
        <Card variant="subtle" className="p-6 space-y-3 border-slate-200">
          <div className="flex items-center gap-2 text-amber-800 font-bold text-sm">
            <ShieldCheck className="w-4 h-4 text-amber-600" />
            4. Bayesian Reliability Shrinkage & Confidence Tiers
          </div>
          <p className="text-xs text-[#475569] leading-relaxed">
            Small samples induce extreme outliers. To prevent unproven players from artificially topping leaderboards, empirical Bayes shrinkage pulls small-sample scores toward the population mean:
          </p>
          <ul className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono pt-2">
            <li className="p-2.5 rounded bg-white border border-amber-300 text-amber-900 font-bold shadow-xs">
              High Confidence: ≥100 balls & ≥8 matches
            </li>
            <li className="p-2.5 rounded bg-white border border-blue-300 text-blue-900 font-bold shadow-xs">
              Medium Confidence: ≥50 balls & ≥4 matches
            </li>
            <li className="p-2.5 rounded bg-white border border-slate-200 text-[#64748B] font-bold shadow-xs">
              Low Confidence: &lt;50 balls under pressure
            </li>
          </ul>
        </Card>
      </div>

      {/* Prominent Formal Disclaimer */}
      <div className="p-5 rounded-2xl border border-pink-200 bg-pink-50/60 flex items-start gap-3.5 shadow-xs">
        <AlertTriangle className="w-5 h-5 text-[#EC008C] flex-shrink-0 mt-0.5" />
        <div className="text-xs text-[#475569] leading-relaxed">
          <strong className="text-[#0F172A] font-semibold block mb-0.5">
            Methodological Notice & Descriptive Scope
          </strong>
          The Clutch Performance Rating Index (CPRI) is a composite descriptive and diagnostic index quantifying historical performance execution under high match leverage (PI ≥ 50). It is not a deterministic forecast or direct guarantee of future single-match performance. All rankings, components, and statistical weights are frozen under the Phase 3.5 production freeze.
        </div>
      </div>
    </div>
  )
}
