"""
Adaptive Learning System Lab - Core Engine
BKT + SM-2 + Decision Logic + Simulation Loop
"""

import numpy as np
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta
from collections import defaultdict
import math

# ─────────────────────────────────────────
#  BKT MODULE
# ─────────────────────────────────────────
class BKTModel:
    """Bayesian Knowledge Tracing"""
    def __init__(self, p_init=0.3, p_transit=0.1, p_slip=0.1, p_guess=0.2):
        self.p_init = p_init
        self.p_transit = p_transit
        self.p_slip = p_slip
        self.p_guess = p_guess

    def update(self, p_know, correct):
        if correct:
            p_correct_given_know = 1 - self.p_slip
            p_correct_given_not_know = self.p_guess
        else:
            p_correct_given_know = self.p_slip
            p_correct_given_not_know = 1 - self.p_guess

        p_correct = p_correct_given_know * p_know + p_correct_given_not_know * (1 - p_know)
        if p_correct == 0:
            p_correct = 1e-6

        # Posterior
        p_know_given_obs = (p_correct_given_know * p_know) / p_correct
        # Learning
        p_know_new = p_know_given_obs + (1 - p_know_given_obs) * self.p_transit
        return float(np.clip(p_know_new, 0.01, 0.99))

    def predict_correct(self, p_know):
        return p_know * (1 - self.p_slip) + (1 - p_know) * self.p_guess


# ─────────────────────────────────────────
#  SM-2 MODULE
# ─────────────────────────────────────────
class SM2Model:
    """Spaced Repetition Scheduling (SM-2)"""
    def __init__(self):
        self.default_ef = 2.5
        self.min_ef = 1.3

    def initial_state(self):
        return {"interval": 1, "ef": self.default_ef, "reps": 0, "next_review": 0}

    def update(self, state, quality, current_step):
        """quality: 0-5 (derived from correctness)"""
        ef = state["ef"]
        reps = state["reps"]
        interval = state["interval"]

        if quality >= 3:
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 6
            else:
                interval = round(interval * ef)
            reps += 1
            ef = ef + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
            ef = max(self.min_ef, ef)
        else:
            reps = 0
            interval = 1

        return {
            "interval": interval,
            "ef": round(ef, 4),
            "reps": reps,
            "next_review": current_step + interval
        }

    def is_due(self, state, current_step):
        return current_step >= state.get("next_review", 0)

    def classify_timing(self, state, current_step):
        due = state.get("next_review", 0)
        diff = current_step - due
        if diff < -2:
            return "early"
        elif diff > 2:
            return "late"
        else:
            return "optimal"


# ─────────────────────────────────────────
#  DECISION ENGINE
# ─────────────────────────────────────────
class DecisionEngine:
    """Selects next skill based on strategy"""

    STRATEGIES = ["adaptive", "random", "fixed_sequence", "weakest_first", "review_based"]

    def __init__(self, strategy="adaptive"):
        self.strategy = strategy

    def select(self, skills, knowledge, sm2_states, current_step):
        if self.strategy == "random":
            return random.choice(skills)
        elif self.strategy == "fixed_sequence":
            return skills[current_step % len(skills)]
        elif self.strategy == "weakest_first":
            return min(skills, key=lambda s: knowledge.get(s, 0.3))
        elif self.strategy == "review_based":
            sm2 = SM2Model()
            due = [s for s in skills if sm2.is_due(sm2_states.get(s, sm2.initial_state()), current_step)]
            if due:
                return min(due, key=lambda s: knowledge.get(s, 0.3))
            return min(skills, key=lambda s: knowledge.get(s, 0.3))
        else:  # adaptive
            sm2 = SM2Model()
            due = [s for s in skills if sm2.is_due(sm2_states.get(s, sm2.initial_state()), current_step)]
            unmastered = [s for s in skills if knowledge.get(s, 0.3) < 0.8]
            if due and unmastered:
                candidates = [s for s in due if s in unmastered]
                if candidates:
                    return min(candidates, key=lambda s: knowledge.get(s, 0.3))
            if unmastered:
                return min(unmastered, key=lambda s: knowledge.get(s, 0.3))
            if due:
                return due[0]
            return random.choice(skills)


# ─────────────────────────────────────────
#  SIMULATION ENGINE
# ─────────────────────────────────────────
class SimulationEngine:
    def __init__(self, bkt_params=None, max_steps=50, mastery_threshold=0.8):
        params = bkt_params or {}
        self.bkt = BKTModel(**params)
        self.sm2 = SM2Model()
        self.max_steps = max_steps
        self.mastery_threshold = mastery_threshold

    def simulate_student(self, student_id, skills, strategy="adaptive", ability=0.5):
        engine = DecisionEngine(strategy)
        knowledge = {s: self.bkt.p_init for s in skills}
        sm2_states = {s: self.sm2.initial_state() for s in skills}
        log = []
        mastery_steps = {}

        for step in range(self.max_steps):
            skill = engine.select(skills, knowledge, sm2_states, step)
            p_know = knowledge[skill]
            p_correct = self.bkt.predict_correct(p_know) * (0.5 + ability)
            p_correct = min(0.99, max(0.01, p_correct))
            correct = 1 if random.random() < p_correct else 0

            old_know = p_know
            new_know = self.bkt.update(p_know, correct)
            knowledge[skill] = new_know

            quality = 4 if correct else 1
            timing = self.sm2.classify_timing(sm2_states[skill], step)
            sm2_states[skill] = self.sm2.update(sm2_states[skill], quality, step)

            if new_know >= self.mastery_threshold and skill not in mastery_steps:
                mastery_steps[skill] = step

            log.append({
                "student_id": student_id,
                "step": step,
                "skill": skill,
                "correct": correct,
                "p_know_before": round(old_know, 4),
                "p_know_after": round(new_know, 4),
                "strategy": strategy,
                "timing": timing,
                "ability": round(ability, 3)
            })

        return {
            "log": log,
            "final_knowledge": knowledge,
            "mastery_steps": mastery_steps,
            "student_id": student_id,
            "strategy": strategy
        }

    def run_experiment(self, dataset_name, skills, n_students=30, strategies=None):
        if strategies is None:
            strategies = DecisionEngine.STRATEGIES

        all_results = []
        strategy_metrics = {}

        for strategy in strategies:
            strat_logs = []
            for i in range(n_students):
                ability = np.random.beta(2, 2)
                result = self.simulate_student(
                    student_id=f"{dataset_name}_s{i}",
                    skills=skills,
                    strategy=strategy,
                    ability=ability
                )
                strat_logs.append(result)
                all_results.extend(result["log"])

            # Compute metrics
            gains, mastery_counts, timing_dist = [], [], defaultdict(int)
            for r in strat_logs:
                init = sum(self.bkt.p_init for _ in r["final_knowledge"]) / len(r["final_knowledge"])
                final = sum(r["final_knowledge"].values()) / len(r["final_knowledge"])
                gains.append(final - init)
                mastery_counts.append(len(r["mastery_steps"]))
                for log_entry in r["log"]:
                    timing_dist[log_entry["timing"]] += 1

            total_timing = sum(timing_dist.values()) or 1
            strategy_metrics[strategy] = {
                "avg_learning_gain": round(float(np.mean(gains)), 4),
                "avg_mastery_count": round(float(np.mean(mastery_counts)), 2),
                "avg_steps_to_mastery": self.max_steps,
                "skill_coverage": round(float(np.mean(mastery_counts)) / len(skills), 4),
                "optimal_review_pct": round(timing_dist["optimal"] / total_timing, 4),
                "early_review_pct": round(timing_dist["early"] / total_timing, 4),
                "late_review_pct": round(timing_dist["late"] / total_timing, 4),
            }

        return {
            "dataset": dataset_name,
            "skills": skills,
            "n_students": n_students,
            "strategies": strategies,
            "strategy_metrics": strategy_metrics,
            "all_logs": all_results
        }
