import argparse, json, subprocess, time, os, sys, shlex, pathlib

def run_pytest(project_dir, timeout_s=900):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.join(project_dir, "src")) + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, "-m", "pytest", "-q"]
    start = time.time()
    try:
        p = subprocess.run(cmd, cwd=project_dir, env=env, capture_output=True, text=True, timeout=timeout_s)
        dur = time.time() - start
        passed = 0
        total = 0
        for line in (p.stdout + "\n" + p.stderr).splitlines():
            if " passed" in line and " warnings" in line:
                # e.g., '2 passed, 1 warning in 0.10s'
                parts = line.split()
                try:
                    passed = int(parts[0])
                except Exception:
                    pass
            if " failed" in line and " passed" in line:
                # capture total roughly
                pass
        return {"returncode": p.returncode, "duration_s": round(dur, 3), "stdout": p.stdout, "stderr": p.stderr, "passed": passed}
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "duration_s": timeout_s, "stdout": "", "stderr": "timeout", "passed": 0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, choices=["p1","p2","p3"])
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()
    proj_map = {
        "p1": "../project1_kb",
        "p2": "../project2_board",
        "p3": "../project3_scheduler",
    }
    proj_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), proj_map[args.project]))
    res = run_pytest(proj_dir, args.timeout)
    result = {
        "project": args.project,
        "completed": int(res["returncode"] == 0),
        "duration_s": res["duration_s"],
        "passed_tests_estimate": res["passed"],
        "returncode": res["returncode"],
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
