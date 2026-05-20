#!/usr/bin/env python3
"""
FloraFlow — Local Launcher
──────────────────────────
  python start.py          Monolithic mode: builds React, Flask serves everything
                           on http://localhost:5001

  python start.py --dev    Dev mode: Flask API only on :5001
                           Run 'npm run dev' in frontend/ for the UI on :5173

  python start.py --build  Force a fresh frontend build before starting

Requirements
  Python 3.10+   https://python.org
  Node.js 18+    https://nodejs.org
  pip (comes with Python)
"""
import os
import sys
import subprocess
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")
DIST = os.path.join(FRONTEND, "dist")
REQ = os.path.join(BACKEND, "requirements-local.txt")

DEV_MODE = "--dev" in sys.argv
FORCE_BUILD = "--build" in sys.argv


def banner(msg):
    print(f"\n  {msg}")


def sh(cmd, cwd=None, capture=False):
    """Run a shell command; exit on failure."""
    result = subprocess.run(cmd, shell=True, cwd=cwd,
                            capture_output=capture, text=capture)
    if result.returncode != 0:
        print(f"\n  ERROR: command failed: {cmd}")
        sys.exit(result.returncode)
    return result


def check_tools():
    """Verify Python and Node are available."""
    if sys.version_info < (3, 10):
        print("  Python 3.10 or newer is required.")
        sys.exit(1)

    if not DEV_MODE:
        if shutil.which("node") is None:
            print("  Node.js not found. Install from https://nodejs.org")
            sys.exit(1)
        if shutil.which("npm") is None:
            print("  npm not found. Install from https://nodejs.org")
            sys.exit(1)


def install_python_deps():
    banner("Installing Python dependencies...")
    sh(f'"{sys.executable}" -m pip install -r "{REQ}" -q')
    print("  Done.")


def install_node_deps():
    nm = os.path.join(FRONTEND, "node_modules")
    if not os.path.isdir(nm):
        banner("Installing Node.js dependencies...")
        sh("npm install", cwd=FRONTEND)
        print("  Done.")


def build_frontend():
    banner("Building frontend (React → dist/)...")
    sh("npm run build", cwd=FRONTEND)
    print("  Done.")


def main():
    print("\n" + "─" * 50)
    print("  FloraFlow — Local Setup")
    print("─" * 50)

    check_tools()
    install_python_deps()

    if DEV_MODE:
        banner("Starting in dev mode (API only)...")
        print("  Flask API → http://localhost:5001/api/v1")
        print("  Run 'npm run dev' inside frontend/ for the UI on :5173")
        print()
        os.environ["FLASK_ENV"] = "local"
        os.environ["SERVE_STATIC"] = "0"
    else:
        install_node_deps()

        if FORCE_BUILD or not os.path.isdir(DIST):
            build_frontend()
        else:
            banner("Frontend already built (use --build to rebuild).")

        banner("Starting in monolithic mode...")
        print("  Flask serves API + React UI → http://localhost:5001")
        print()
        os.environ["FLASK_ENV"] = "local"
        os.environ["SERVE_STATIC"] = "1"

    # Hand off to run_local.py (replaces this process)
    os.chdir(BACKEND)
    os.execv(sys.executable, [sys.executable, "run_local.py"])


if __name__ == "__main__":
    main()
