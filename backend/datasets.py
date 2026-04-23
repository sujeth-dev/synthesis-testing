"""
Dataset Loader - Synthetic + ASSISTments + EdNet
Normalizes all to: user_id, skill_id, correct, timestamp
"""

import numpy as np
import pandas as pd
import os
import json
import random
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# ─────────────────────────────────────────
#  SYNTHETIC DATASET GENERATOR
# ─────────────────────────────────────────
def generate_synthetic(n_students=50, n_skills=10, n_interactions=500, seed=42):
    random.seed(seed)
    np.random.seed(seed)

    skill_names = [
        "Algebra Basics", "Linear Equations", "Quadratic Functions",
        "Geometry Fundamentals", "Trigonometry", "Calculus Intro",
        "Statistics", "Probability", "Number Theory", "Combinatorics"
    ][:n_skills]

    records = []
    base_time = datetime(2024, 1, 1)

    for sid in range(n_students):
        ability = np.random.beta(2, 2)
        t = base_time + timedelta(hours=sid * 10)
        for i in range(n_interactions // n_students):
            skill = random.choice(skill_names)
            correct = 1 if random.random() < (0.3 + 0.5 * ability) else 0
            records.append({
                "user_id": f"student_{sid:03d}",
                "skill_id": skill,
                "correct": correct,
                "timestamp": t.isoformat()
            })
            t += timedelta(minutes=random.randint(2, 15))

    df = pd.DataFrame(records)
    path = os.path.join(DATA_DIR, "synthetic.csv")
    df.to_csv(path, index=False)
    return df, skill_names

# ─────────────────────────────────────────
#  ASSISTMENTS DATASET (Simulated Structure)
# ─────────────────────────────────────────
def generate_assistments(n_students=40, seed=7):
    """Generate realistic ASSISTments-style data"""
    random.seed(seed)
    np.random.seed(seed)

    skill_names = [
        "Fraction Addition", "Fraction Multiplication", "Decimal Operations",
        "Percent Problems", "Ratio & Proportion", "Integer Operations",
        "Order of Operations", "Distributive Property", "Solving Equations",
        "Inequalities", "Graphing Lines", "Slope & Intercept",
        "Systems of Equations", "Polynomials", "Factoring"
    ]

    records = []
    base_time = datetime(2023, 9, 1)

    for sid in range(n_students):
        ability = np.random.beta(3, 2)
        mastery = {s: np.random.uniform(0.1, 0.4) for s in skill_names}
        t = base_time + timedelta(days=sid)

        for session in range(15):
            n_items = random.randint(8, 20)
            skill = random.choice(skill_names)
            mastery[skill] = min(0.99, mastery[skill] + np.random.uniform(0.02, 0.08))

            for _ in range(n_items):
                p_correct = mastery[skill] * ability * 1.2
                p_correct = min(0.95, max(0.05, p_correct))
                correct = 1 if random.random() < p_correct else 0
                records.append({
                    "user_id": f"assist_{sid:03d}",
                    "skill_id": skill,
                    "correct": correct,
                    "timestamp": t.isoformat()
                })
                t += timedelta(minutes=random.randint(1, 8))

            t += timedelta(days=random.randint(0, 2))

    df = pd.DataFrame(records)
    path = os.path.join(DATA_DIR, "assistments.csv")
    df.to_csv(path, index=False)
    return df, skill_names

# ─────────────────────────────────────────
#  EDNET DATASET (Simulated Subset)
# ─────────────────────────────────────────
def generate_ednet(n_students=35, seed=13):
    """Generate realistic EdNet-style data"""
    random.seed(seed)
    np.random.seed(seed)

    skill_names = [
        "Grammar Fundamentals", "Reading Comprehension", "Vocabulary Building",
        "Listening Skills", "Writing Basics", "Sentence Structure",
        "Tense Usage", "Prepositions", "Conditionals", "Passive Voice",
        "Reported Speech", "Modal Verbs"
    ]

    difficulty_map = {s: random.uniform(0.3, 0.8) for s in skill_names}
    records = []
    base_time = datetime(2023, 6, 1)

    for sid in range(n_students):
        ability = np.random.beta(2, 3)
        t = base_time + timedelta(hours=random.randint(0, 200))

        for day in range(20):
            daily_skills = random.sample(skill_names, k=random.randint(2, 5))
            for skill in daily_skills:
                n_q = random.randint(3, 12)
                for _ in range(n_q):
                    diff = difficulty_map[skill]
                    p_correct = ability / (ability + diff)
                    p_correct = min(0.95, max(0.05, p_correct))
                    correct = 1 if random.random() < p_correct else 0
                    records.append({
                        "user_id": f"ednet_{sid:03d}",
                        "skill_id": skill,
                        "correct": correct,
                        "timestamp": t.isoformat()
                    })
                    t += timedelta(minutes=random.randint(1, 5))
            t += timedelta(hours=random.randint(4, 48))

    df = pd.DataFrame(records)
    path = os.path.join(DATA_DIR, "ednet.csv")
    df.to_csv(path, index=False)
    return df, skill_names

# ─────────────────────────────────────────
#  UNIFIED LOADER
# ─────────────────────────────────────────
DATASET_REGISTRY = {
    "synthetic": {
        "label": "Synthetic Simulation",
        "description": "50 students, 10 math skills, probability-based responses",
        "generator": generate_synthetic,
        "file": "synthetic.csv"
    },
    "assistments": {
        "label": "ASSISTments (Math)",
        "description": "40 students, 15 math skills, ASSISTments-style structure",
        "generator": generate_assistments,
        "file": "assistments.csv"
    },
    "ednet": {
        "label": "EdNet (English Learning)",
        "description": "35 students, 12 English skills, EdNet-style difficulty model",
        "generator": generate_ednet,
        "file": "ednet.csv"
    }
}

def load_dataset(name):
    info = DATASET_REGISTRY.get(name)
    if not info:
        raise ValueError(f"Unknown dataset: {name}")

    path = os.path.join(DATA_DIR, info["file"])
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(path):
        print(f"[Loader] Generating {name} dataset...")
        df, skills = info["generator"]()
    else:
        df = pd.read_csv(path)
        skills = sorted(df["skill_id"].unique().tolist())

    stats = {
        "n_users": int(df["user_id"].nunique()),
        "n_skills": int(df["skill_id"].nunique()),
        "n_interactions": int(len(df)),
        "avg_correct": round(float(df["correct"].mean()), 4),
        "skills": skills
    }
    return df, skills, stats

def preload_all():
    results = {}
    for name in DATASET_REGISTRY:
        try:
            df, skills, stats = load_dataset(name)
            results[name] = {"stats": stats, "skills": skills}
            print(f"[OK] {name}: {stats['n_users']} users, {stats['n_skills']} skills, {stats['n_interactions']} interactions")
        except Exception as e:
            print(f"[ERR] {name}: {e}")
    return results

if __name__ == "__main__":
    preload_all()
