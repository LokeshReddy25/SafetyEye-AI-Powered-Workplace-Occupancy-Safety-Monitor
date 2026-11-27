"""Run a command and save the exact command + full stdout/stderr to results/raw/<name>.txt.

Usage: python scripts/run_logged.py <name> -- <command ...>
"""
import datetime as dt
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if "--" not in sys.argv:
        print(__doc__)
        return 2
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    i = sys.argv.index("--")
    name, cmd = sys.argv[1], sys.argv[i + 1:]
    exe = ROOT / cmd[0]
    for cand in (exe, exe.with_suffix(".exe")):
        if not Path(cmd[0]).is_absolute() and cand.exists():
            cmd[0] = str(cand)
            break
    out = ROOT / "results" / "raw" / f"{name}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                cwd=ROOT).stdout.strip()
    except OSError:
        commit = "?"
    start = dt.datetime.now()
    with out.open("w", encoding="utf-8") as f:
        f.write(f"# command: {' '.join(cmd)}\n# cwd: {ROOT.name}\n# git: {commit}\n# started: {start.isoformat()}\n\n")
        f.flush()
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace", env={**__import__("os").environ,
                                                                         "PYTHONIOENCODING": "utf-8"})
        for line in proc.stdout:
            sys.stdout.write(line)
            f.write(line)
            f.flush()
        rc = proc.wait()
        end = dt.datetime.now()
        f.write(f"\n# finished: {end.isoformat()}  elapsed_s: {(end - start).total_seconds():.1f}  exit_code: {rc}\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
