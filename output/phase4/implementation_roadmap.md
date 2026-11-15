# SupeRR Intelligence — Phase 4 Implementation Roadmap: AI Scouting Intelligence Engine

**Document Identifier**: `ROADMAP-PHASE4-AI-SCOUTING-v1.0`  
**Parent Framework**: SupeRR Intelligence Platform  
**Target Milestone**: Phase 4 AI Scouting Intelligence Engine  
**Baseline Lock**: Phase 3.5 Frozen CPRI (`CPRI-v1.0.0-PROD-FREEZE`)  
**Status**: ACTIVE EXECUTION BLUEPRINT  

---

## 1. Executive Summary & Phasing Strategy

The objective of Phase 4 is to transform SupeRR Intelligence into an AI-powered cricket scouting platform that translates dense statistical modeling and frozen CPRI metric evaluations into natural language intelligence, tactical insights, and decision-support narratives.

To deliver this system reliably without disrupting frozen production assets, Phase 4 is organized into five structured sub-phases:
1. **Phase 4.1: Architecture, Model Evaluation & Data Integration Plan** *(Foundation — Current)*
2. **Phase 4.2: Data Extraction & Scouting Store Builder** *(Data Layer)*
3. **Phase 4.3: Scouting Data Engine & Prompt Assembler** *(Context & Grounding Layer)*
4. **Phase 4.4: AI Generation Service & Dual-Mode Hugging Face Client** *(Inference Layer)*
5. **Phase 4.5: Verification Guardrails, Anti-Hallucination Tests & Regression Suite** *(Guardrail & Certification Layer)*

```
[Phase 4.1: Architecture & Model Selection] (Completed)
                     │
                     ▼
[Phase 4.2: Scouting Store Builder] (build_scouting_store.py)
   ├── player_scouting_profiles.json (~3.2 MB)
   ├── player_contextual_splits.json (~2.8 MB)
   └── head_to_head_matrix.json (~1.5 MB)
                     │
                     ▼
[Phase 4.3: Scouting Data Engine & Prompt Assembler] (scouting_data_engine.py)
   ├── 7 Core Scouting Feature Interfaces
   └── Strict Grounding Context Builders
                     │
                     ▼
[Phase 4.4: AI Generation Service] (scouting_ai_service.py)
   ├── Dual-Mode Hugging Face Client (Local Qwen2.5-3B + API Qwen2.5-7B)
   └── Deterministic Template Fallback (100% Offline Resilience)
                     │
                     ▼
[Phase 4.5: Verification & Anti-Hallucination Guardrails] (test_phase4.py)
   ├── Metric Consistency & Immutability Verification
   ├── Anti-Hallucination Fact-Checking Regex Suite
   └── Integration into run_all_tests_suite.py (128 -> 150+ tests)
```

---

## 2. Detailed Phase Breakdowns

### Phase 4.1: Foundation, Architecture & Model Evaluation *(Status: COMPLETE)*
* **Objective**: Define system boundaries, establish immutability rules, evaluate candidate language models, and specify the data integration architecture.
* **Deliverables**:
  1. `output/phase4/phase4_architecture.md`: 5-layer system design, specs for the 7 core scouting features, and anti-hallucination protocols.
  2. `output/phase4/huggingface_model_evaluation.md`: Comparative benchmark of generation, QA, and semantic search models; dual-mode recommendation (`Qwen2.5-3B-Instruct` / `Qwen2.5-7B-Instruct` + `all-MiniLM-L6-v2`).
  3. `output/phase4/data_integration_plan.md`: Zero-duplication data transformation spec distilling 150 MB of raw deliveries into < 8 MB fast query stores.
  4. `output/phase4/implementation_roadmap.md`: This execution blueprint.

---

### Phase 4.2: Data Extraction & Scouting Store Builder *(Next Immediate Step)*
* **Objective**: Create the offline feature distillation pipeline that extracts player contextual splits, bowler-type matchups, match-phase breakdowns, and head-to-head records into fast, structured JSON stores.
* **Core Script**: `build_scouting_store.py`
* **Inputs**:
  - `output/phase3_5/official_rankings.csv` & `official_rankings.json`
  - `output/phase3_5/eligibility_and_uncertainty.csv`
  - `output/phase3_3/all_batter_rankings.csv` & `all_bowler_rankings.csv`
  - `output/processed/deliveries_enriched.csv`
* **Outputs Generated**:
  1. `output/phase4/data/player_scouting_profiles.json`: Unified player dictionary indexing CPRI scores, ranks, component percentiles, baseline metrics, and peer comparisons.
  2. `output/phase4/data/player_contextual_splits.json`: Detailed splits by match phase (Powerplay, Middle, Death), opposition bowling type (Pace, Off-spin, Leg-spin, SLA), and pressure regime ($\text{PI} < 50$ vs $\text{PI} \ge 50$).
  3. `output/phase4/data/head_to_head_matrix.json`: Ball-by-ball aggregated batter vs. bowler matchup matrix (runs, balls, dismissals, dot balls, strike rate, boundary %).
* **Validation Criteria**:
  - Processing completes under 45 seconds.
  - JSON schemas strictly adhere to definitions in `data_integration_plan.md`.
  - Zero discrepancies with official Phase 3.5 rankings or Phase 3.3 metric aggregates.

---

### Phase 4.3: Scouting Data Engine & Grounded Prompt Assembler
* **Objective**: Implement the Python API that exposes the 7 core scouting queries and constructs bulletproof, fact-grounded context blocks for LLM prompting.
* **Core Module**: `scouting_data_engine.py`
* **Key Components**:
  1. `ScoutingDataEngine` class: In-memory indexing of scouting stores with caching and type safety.
  2. Feature-specific retrieval methods:
     - `get_player_profile(player_name, cohort)`
     - `get_pressure_breakdown(player_name, cohort)`
     - `get_tactical_splits(player_name, cohort)`
     - `get_head_to_head(batter_name, bowler_name)`
     - `get_cohort_comparison(player_a, player_b, cohort)`
  3. `PromptAssembler` class:
     - Context injection with mandatory JSON schema boundaries.
     - Insertion of the **System Guardrail Prompt** (anti-hallucination directive).
     - Standardized variable substitution across all 7 prompt templates.
* **Validation Criteria**:
  - Query latency < 1.0 ms per player profile lookup.
  - Formatted prompt contexts include 100% of required ground-truth stats and 0% placeholder tokens.

---

### Phase 4.4: AI Generation Service & Dual-Mode Hugging Face Client
* **Objective**: Build the inference orchestration service that supports local CPU generation, Hugging Face Serverless API inference, and offline deterministic template generation.
* **Core Module**: `scouting_ai_service.py`
* **Architecture Implementation**:
  1. **Tier 1: Free Hugging Face Serverless API Client**:
     - Endpoint: `Qwen/Qwen2.5-7B-Instruct`
     - Authenticated via `HUGGINGFACEHUB_API_TOKEN` environment variable.
     - Structured JSON output mode with retry logic and exponential backoff.
  2. **Tier 2: Local Lightweight CPU Pipeline**:
     - Model: `Qwen/Qwen2.5-3B-Instruct` (or `Llama-3.2-3B-Instruct`) via `transformers`.
     - Int4 / Int8 quantized execution using PyTorch CPU.
  3. **Tier 3: Deterministic Rule-Based Fallback Engine**:
     - Pre-compiled scouting narrative templates covering all 7 features.
     - Zero AI model dependency: guarantees 100% uptime and offline testability.
* **Validation Criteria**:
  - Graceful degradation: if API is unreachable and local model is uninstalled, system immediately falls back to Tier 3 without throwing an unhandled exception.
  - Zero hallucination of numbers: all generated numerical values match the grounded prompt context exactly.

---

### Phase 4.5: Verification Guardrails, Anti-Hallucination Tests & Regression Suite
* **Objective**: Develop comprehensive test coverage verifying statistical immutability, output schema compliance, and factual accuracy across all generated reports.
* **Core Scripts**:
  - `test_phase4_scouting_engine.py` (Tests 1–15: data loading, retrieval, prompt assembly).
  - `test_phase4_ai_guardrails.py` (Tests 16–30: numerical fact verification, regex metric audits, forbidden phrase detection).
  - Integration with master test suite `run_all_tests_suite.py` (bringing total test suite count from 128 to 150+ tests).
* **Guaranteed Guardrail Checks**:
  1. Every CPRI score, rank, and metric mentioned in AI output must exist in the input prompt.
  2. AI output cannot contain fabricated statistical claims (e.g., claiming a strike rate of 165.0 when ground truth is 142.3).
  3. Clear labelling distinguishing verified historical stats from tactical scouting opinions.
  4. Complete regression check confirming all Phase 1–3.5 test cases continue to pass with 0 failures.

---

## 3. Timeline, Dependencies, and Milestones

| Sub-Phase | Estimated Scope | Primary Output Artifacts | Primary Dependencies | Status |
|:---|:---|:---|:---|:---:|
| **Phase 4.1** | Foundation & Architecture | Architecture spec, Model evaluation, Integration plan, Roadmap | Phase 3.5 Frozen Outputs | **COMPLETE** |
| **Phase 4.2** | Data Store Builder | `build_scouting_store.py`, 3 JSON scouting stores (< 8 MB total) | `deliveries_enriched.csv`, Phase 3.5 rankings | **READY** |
| **Phase 4.3** | Query API & Prompting | `scouting_data_engine.py`, 7 Prompt Context Assemblers | Phase 4.2 JSON Stores | PENDING |
| **Phase 4.4** | AI Inference Service | `scouting_ai_service.py`, Local / API Hugging Face connectors | `transformers`, `huggingface_hub` | PENDING |
| **Phase 4.5** | Guardrails & Test Suite | `test_phase4.py`, 25+ new tests integrated into master test suite | All Phase 4 modules | PENDING |

---

## 4. Resource Allocation & Environment Constraints

1. **Python Environment**: Python 3.14 on Windows 64-bit AMD64.
2. **Compute Profile**: CPU execution (`torch 2.10.0+cpu`). Memory ceiling capped at $\le 4.0\text{ GB}$ RAM by utilizing JSON stores and quantized/small parameter models.
3. **Storage Profile**: Pre-aggregated JSON stores require $\approx 7.5\text{ MB}$, eliminating repetitive scans of the $150\text{ MB}$ raw CSV file during interactive queries.
4. **Third-Party API Cost**: \$0.00 (leveraging Hugging Face Serverless Free Tier API and Apache 2.0 open-weight weights).
5. **No Regressions**: Phase 1, Phase 2, Phase 3, and Phase 3.5 test suites must maintain 100% pass rates across all runs.

---

## 5. Immediate Next Implementation Step

Proceed immediately to **Phase 4.2**:
- Implement `build_scouting_store.py` in the root script directory.
- Execute the script to generate:
  - `output/phase4/data/player_scouting_profiles.json`
  - `output/phase4/data/player_contextual_splits.json`
  - `output/phase4/data/head_to_head_matrix.json`
- Validate that all 60 ranked players (40 Official + 20 Provisional) are completely mapped with zero data loss.
