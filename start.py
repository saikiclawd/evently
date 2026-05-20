#!/usr/bin/env python3
"""
FloraFlow — Local Launcher
──────────────────────────
  python3 start.py          Monolithic mode: builds React, Flask serves everything
                            on http://localhost:5001

  python3 start.py --dev    Dev mode: Flask API only on :5001
                            Run 'npm run dev' in frontend/ for the UI on :5173

  python3 start.py --build  Force a fresh frontend build before starting

Requirements
  Python 3.10+   https://python.org
  Node.js 18+    https://nodejs.org
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
VENV = os.path.join(ROOT, ".venv")

DEV_MODE = "--dev" in sys.argv
FORCE_BUILD = "--build" in sys.argv

# Python executable inside the venv
if sys.platform == "win32":
    VENV_PYTHON = os.path.join(VENV, "Scripts", "python.exe")
else:
    VENV_PYTHON = os.path.join(VENV, "bin", "python3")


def banner(msg):
    print(f"\n  {msg}")


def sh(cmd, cwd=None):
    """Run a shell command; exit on failure."""
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"\n  ERROR: command failed: {cmd}")
        sys.exit(result.returncode)


def ensure_venv():
    """Create .venv if it doesn't exist, then install deps into it."""
    if not os.path.isfile(VENV_PYTHON):
        banner("Creating virtual environment (.venv)...")
        sh(f'"{sys.executable}" -m venv "{VENV}"')
        print("  Done.")

    banner("Installing Python dependencies into .venv...")
    sh(f'"{VENV_PYTHON}" -m pip install -r "{REQ}" -q --upgrade')
    print("  Done.")


def check_tools():
    v = sys.version_info
    if v < (3, 10):
        print("  Python 3.10 or newer is required.")
        sys.exit(1)
    if v >= (3, 14):
        print(f"  Python {v.major}.{v.minor} is pre-release and has known macOS issues.")
        print("  Please run with Python 3.12 or 3.13:")
        print("    brew install python@3.13")
        print("    python3.13 start.py")
        sys.exit(1)

    if not DEV_MODE:
        if shutil.which("node") is None:
            print("  Node.js not found. Install from https://nodejs.org")
            sys.exit(1)
        if shutil.which("npm") is None:
            print("  npm not found. Install from https://nodejs.org")
            sys.exit(1)


def install_node_deps():
    if not os.path.isdir(os.path.join(FRONTEND, "node_modules")):
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
    ensure_venv()

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

    # Replace this process with the venv Python running run_local.py
    os.chdir(BACKEND)
    os.execv(VENV_PYTHON, [VENV_PYTHON, "run_local.py"])


if __name__ == "__main__":
    main()
