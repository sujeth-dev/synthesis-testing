"""
Adaptive Learning System Lab - Flask API Server
Serves experiment results to the dashboard
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, sys, json, threading, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from engine import SimulationEngine, DecisionEngine
from datasets import load_dataset, DATASET_REGISTRY, preload_all
from metrics import compute_all_metrics
from report_generator import generate_report_data

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"))
CORS(app)

OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# In-memory cache
_cache = {}
_run_status = {"running": False, "progress": 0, "message": "Idle", "current_dataset": None}

# ─────────────────────────────────────────
#  ROUTES — STATIC
# ─────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_files(path):
    full = os.path.join(app.static_folder, path)
    if os.path.exists(full):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# ─────────────────────────────────────────
#  ROUTES — DATASETS
# ─────────────────────────────────────────
@app.route("/api/datasets")
def get_datasets():
    result = {}
    for name, info in DATASET_REGISTRY.items():
        result[name] = {
            "label": info["label"],
            "description": info["description"],
        }
    return jsonify(result)

@app.route("/api/dataset/<name>/info")
def dataset_info(name):
    try:
        _, skills, stats = load_dataset(name)
        return jsonify({"stats": stats, "skills": skills})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ─────────────────────────────────────────
#  ROUTES — EXPERIMENT RUN
# ─────────────────────────────────────────
@app.route("/api/run", methods=["POST"])
def run_experiment():
    global _run_status
    if _run_status["running"]:
        return jsonify({"error": "Experiment already running"}), 409

    body = request.json or {}
    dataset_name = body.get("dataset", "synthetic")
    n_students = int(body.get("n_students", 30))
    max_steps = int(body.get("max_steps", 50))
    mastery_threshold = float(body.get("mastery_threshold", 0.8))
    strategies = body.get("strategies", DecisionEngine.STRATEGIES)
    bkt_params = body.get("bkt_params", {})

    def run_bg():
        global _run_status
        _run_status = {"running": True, "progress": 5, "message": "Loading dataset...", "current_dataset": dataset_name}
        try:
            _, skills, stats = load_dataset(dataset_name)
            _run_status["progress"] = 15
            _run_status["message"] = f"Loaded {stats['n_skills']} skills, {stats['n_users']} users"

            engine = SimulationEngine(bkt_params=bkt_params, max_steps=max_steps, mastery_threshold=mastery_threshold)
            _run_status["progress"] = 20
            _run_status["message"] = "Running simulation..."

            results = engine.run_experiment(dataset_name, skills, n_students=n_students, strategies=strategies)
            _run_status["progress"] = 70
            _run_status["message"] = "Computing metrics..."

            metrics = compute_all_metrics(results)
            _run_status["progress"] = 85
            _run_status["message"] = "Generating report..."

            report = generate_report_data(results, metrics, stats)
            _run_status["progress"] = 95

            cache_key = f"{dataset_name}_{datetime.now().strftime('%H%M%S')}"
            _cache[cache_key] = {
                "results": results,
                "metrics": metrics,
                "report": report,
                "dataset_stats": stats,
                "config": body,
                "timestamp": datetime.now().isoformat()
            }
            _cache["latest"] = _cache[cache_key]

            # Save to disk
            out_path = os.path.join(OUTPUTS_DIR, f"experiment_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(out_path, "w") as f:
                json.dump({k: v for k, v in _cache["latest"].items() if k != "results"}, f, indent=2, default=str)

            _run_status["progress"] = 100
            _run_status["message"] = f"Complete! Cache key: {cache_key}"
            _run_status["last_key"] = cache_key
        except Exception as e:
            import traceback
            _run_status["message"] = f"Error: {str(e)}"
            _run_status["error"] = traceback.format_exc()
        finally:
            _run_status["running"] = False

    t = threading.Thread(target=run_bg)
    t.daemon = True
    t.start()
    return jsonify({"status": "started", "message": "Experiment running in background"})

@app.route("/api/status")
def get_status():
    return jsonify(_run_status)

@app.route("/api/results")
def get_results():
    if "latest" not in _cache:
        return jsonify({"error": "No results yet. Run an experiment first."}), 404
    data = _cache["latest"]
    # Slim down logs for transfer
    payload = {
        "metrics": data["metrics"],
        "report": data["report"],
        "dataset_stats": data["dataset_stats"],
        "config": data.get("config", {}),
        "timestamp": data["timestamp"]
    }
    return jsonify(payload)

@app.route("/api/results/full")
def get_full_results():
    if "latest" not in _cache:
        return jsonify({"error": "No results yet"}), 404
    data = _cache["latest"]
    # Include first 200 log entries
    results_copy = dict(data["results"])
    results_copy["all_logs"] = results_copy.get("all_logs", [])[:200]
    return jsonify({
        "metrics": data["metrics"],
        "report": data["report"],
        "dataset_stats": data["dataset_stats"],
        "results_sample": results_copy
    })

# ─────────────────────────────────────────
#  ROUTES — QUICK PRECOMPUTE (startup)
# ─────────────────────────────────────────
@app.route("/api/precompute", methods=["POST"])
def precompute_all():
    def run_all():
        for ds in DATASET_REGISTRY:
            try:
                _, skills, stats = load_dataset(ds)
                engine = SimulationEngine(max_steps=40)
                results = engine.run_experiment(ds, skills, n_students=20)
                metrics = compute_all_metrics(results)
                report = generate_report_data(results, metrics, stats)
                _cache[ds] = {
                    "results": results, "metrics": metrics,
                    "report": report, "dataset_stats": stats,
                    "timestamp": datetime.now().isoformat()
                }
                print(f"[Precompute] Done: {ds}")
            except Exception as e:
                print(f"[Precompute] Error {ds}: {e}")
        _cache["latest"] = _cache.get("synthetic", {})
        print("[Precompute] All datasets ready.")
    t = threading.Thread(target=run_all)
    t.daemon = True
    t.start()
    return jsonify({"status": "started"})

@app.route("/api/cached")
def get_cached():
    keys = [k for k in _cache.keys() if k != "latest"]
    return jsonify({"cached": keys, "has_latest": "latest" in _cache})

@app.route("/api/cached/<key>")
def get_cached_key(key):
    if key not in _cache:
        return jsonify({"error": "Not found"}), 404
    data = _cache[key]
    return jsonify({"metrics": data.get("metrics"), "report": data.get("report"), "dataset_stats": data.get("dataset_stats")})

@app.route("/api/strategies")
def get_strategies():
    return jsonify({"strategies": DecisionEngine.STRATEGIES})

if __name__ == "__main__":
    print("=" * 60)
    print("  Adaptive Learning System Lab - Server")
    print("  URL: http://localhost:5000")
    print("=" * 60)
    # Auto precompute on start
    import requests as _req
    def _auto_precompute():
        time.sleep(2)
        try:
            _req.post("http://localhost:5000/api/precompute")
        except:
            pass
    t = threading.Thread(target=_auto_precompute)
    t.daemon = True
    t.start()
    app.run(debug=False, port=5000, host="0.0.0.0")
