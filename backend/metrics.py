"""
Metrics Computation Module
Learning-focused metrics for the adaptive system
"""

import numpy as np
from collections import defaultdict


def compute_all_metrics(results):
    strategy_metrics = results.get("strategy_metrics", {})
    all_logs = results.get("all_logs", [])
    skills = results.get("skills", [])

    # Per-step learning curves (averaged across students per strategy)
    learning_curves = {}
    mastery_curves = {}

    logs_by_strategy = defaultdict(list)
    for entry in all_logs:
        logs_by_strategy[entry["strategy"]].append(entry)

    for strategy, logs in logs_by_strategy.items():
        logs_by_student = defaultdict(list)
        for e in logs:
            logs_by_student[e["student_id"]].append(e)

        max_steps = max((e["step"] for e in logs), default=0) + 1
        step_know = defaultdict(list)
        step_mastery = defaultdict(list)

        for sid, slogs in logs_by_student.items():
            slogs.sort(key=lambda x: x["step"])
            skill_know = {}
            for e in slogs:
                skill_know[e["skill"]] = e["p_know_after"]
                avg_know = np.mean(list(skill_know.values()))
                mastered = sum(1 for v in skill_know.values() if v >= 0.8) / max(len(skills), 1)
                step_know[e["step"]].append(avg_know)
                step_mastery[e["step"]].append(mastered)

        lc, mc = [], []
        for step in range(min(max_steps, 50)):
            if step_know[step]:
                lc.append(round(float(np.mean(step_know[step])), 4))
                mc.append(round(float(np.mean(step_mastery[step])), 4))
            elif lc:
                lc.append(lc[-1])
                mc.append(mc[-1])

        learning_curves[strategy] = lc
        mastery_curves[strategy] = mc

    # Skill heatmap: avg final knowledge per skill per strategy
    skill_heatmap = {}
    for strategy, logs in logs_by_strategy.items():
        skill_finals = defaultdict(list)
        for e in logs:
            skill_finals[e["skill"]].append(e["p_know_after"])
        skill_heatmap[strategy] = {
            s: round(float(np.mean(vals)), 4)
            for s, vals in skill_finals.items()
        }

    # Review timing
    review_timing = {}
    for strategy, logs in logs_by_strategy.items():
        td = defaultdict(int)
        for e in logs:
            td[e.get("timing", "optimal")] += 1
        total = sum(td.values()) or 1
        review_timing[strategy] = {k: round(v / total, 4) for k, v in td.items()}

    # Rolling accuracy (difficulty balance) - window of 10
    rolling_accuracy = {}
    for strategy, logs in logs_by_strategy.items():
        correct_vals = [e["correct"] for e in sorted(logs, key=lambda x: x["step"])]
        window = 10
        ra = []
        for i in range(0, min(len(correct_vals), 500), window):
            chunk = correct_vals[i:i + window]
            ra.append(round(float(np.mean(chunk)), 4))
        rolling_accuracy[strategy] = ra

    # Parameter sensitivity (BKT p_init impact)
    sensitivity = _compute_sensitivity(skills)

    # Summary table
    summary = []
    for strat, m in strategy_metrics.items():
        summary.append({
            "strategy": strat,
            "learning_gain": m.get("avg_learning_gain", 0),
            "mastery_count": m.get("avg_mastery_count", 0),
            "skill_coverage": m.get("skill_coverage", 0),
            "optimal_review_pct": m.get("optimal_review_pct", 0),
        })
    summary.sort(key=lambda x: x["learning_gain"], reverse=True)

    return {
        "strategy_metrics": strategy_metrics,
        "learning_curves": learning_curves,
        "mastery_curves": mastery_curves,
        "skill_heatmap": skill_heatmap,
        "review_timing": review_timing,
        "rolling_accuracy": rolling_accuracy,
        "sensitivity": sensitivity,
        "summary_table": summary
    }


def _compute_sensitivity(skills):
    """Simulate how BKT p_init affects learning gain"""
    from engine import SimulationEngine
    import random
    random.seed(99)
    np.random.seed(99)

    p_inits = [0.1, 0.2, 0.3, 0.4, 0.5]
    gains = []
    for pi in p_inits:
        engine = SimulationEngine(bkt_params={"p_init": pi}, max_steps=30)
        results = engine.run_experiment("sensitivity", skills[:5], n_students=10, strategies=["adaptive"])
        gain = results["strategy_metrics"]["adaptive"]["avg_learning_gain"]
        gains.append(gain)
    return {"p_init_values": p_inits, "learning_gains": [round(g, 4) for g in gains]}
