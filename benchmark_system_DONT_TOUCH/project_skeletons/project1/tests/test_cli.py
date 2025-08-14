import subprocess, sys, os, tempfile

def run_cli(args):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath("src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-m", "kb.cli", *args], capture_output=True, text=True, env=env)

def test_cli_ingest_nonexistent():
    p = run_cli(["ingest", "no/such/path"])
    assert p.returncode == 1
    assert "path not found" in p.stdout.lower()
