# Adaptive Learning System Lab v1.0

**BKT (Bayesian Knowledge Tracing) + SM-2 (Spaced Repetition) + Adaptive Decision Engine**

## Quick Start

### Windows
```
Double-click: start.bat
```

### Mac / Linux
```bash
chmod +x start.sh
./start.sh
```

The browser opens automatically at **http://localhost:5000**

---

## What's Inside

### Core Engine
- **BKT Module** — Tracks P(know) per skill per student
- **SM-2 Module** — Spaced repetition scheduling
- **Decision Engine** — 5 strategies: Adaptive, Random, Fixed Sequence, Weakest First, Review Based
- **Simulation Loop** — Virtual learners with ability + noise (slip, guess)

### Datasets (Auto-Generated)
| Dataset | Users | Skills | Domain |
|---------|-------|--------|--------|
| Synthetic | 50 | 10 | Math simulation |
| ASSISTments | 40 | 15 | Math (ASSISTments-style) |
| EdNet | 35 | 12 | English learning (EdNet-style) |

### Dashboard Tabs
1. **Overview** — KPI cards + strategy comparison + review timing
2. **Learning Curves** — P(know) over time + mastery progress + difficulty balance
3. **Strategy Analysis** — Radar chart + sensitivity + timing distribution
4. **Skill Heatmap** — Final knowledge per skill per strategy
5. **Report Outputs** — All placeholders: VALUES, TABLES, GRAPHS, TEXT

### Modes
- **Mode A (Full Run)** — Press ▶ Run, system completes automatically
- **Mode B (Precompute)** — Press ⚡ Precompute All, all 3 datasets load

---

## Report Placeholders Generated
- `[VALUE: Number of Users]`, `[VALUE: Average Learning Gain]`, etc.
- `[TABLE: Strategy Comparison]`, `[TABLE: Dataset Statistics]`
- `[GRAPH: Learning Gain Curve]`, `[GRAPH: Mastery Progress]`, etc.
- `[TEXT: Key Insights]`, `[TEXT: Limitations]`, etc.

---

## Architecture
```
adaptive_lab/
├── start.bat              ← Windows launcher (full auto)
├── start.sh               ← Mac/Linux launcher
├── requirements.txt
├── backend/
│   ├── server.py          ← Flask API server
│   ├── engine.py          ← BKT + SM-2 + Simulation
│   ├── datasets.py        ← Synthetic + ASSISTments + EdNet
│   ├── metrics.py         ← All learning metrics
│   └── report_generator.py← Report placeholders
├── frontend/
│   └── index.html         ← Full interactive dashboard
├── data/                  ← Auto-generated CSV datasets
└── outputs/               ← Saved experiment JSON results
```

## Requirements
- Python 3.8+
- No manual pip install needed — handled by start script
# synthesis-testing
