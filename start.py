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
import urllib.request

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


def bootstrap_pip():
    """Download get-pip.py and install pip into the venv."""
    get_pip = os.path.join(ROOT, ".get-pip.py")
    banner("Bootstrapping pip (Homebrew ensurepip workaround)...")
    try:
        urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", get_pip)
    except Exception as e:
        print(f"  Could not download get-pip.py: {e}")
        print("  Check your internet connection and try again.")
        sys.exit(1)
    sh(f'"{VENV_PYTHON}" "{get_pip}" -q')
    os.remove(get_pip)
    print("  pip installed.")


def venv_has_pip():
    r = subprocess.run(
        f'"{VENV_PYTHON}" -m pip --version',
        shell=True, capture_output=True
    )
    return r.returncode == 0


def ensure_venv():
    """Create .venv if it doesn't exist, then install deps into it."""
    if not os.path.isfile(VENV_PYTHON) or not venv_has_pip():
        # Clean up any partial venv from a previous failed attempt
        if os.path.isdir(VENV):
            shutil.rmtree(VENV)

        banner("Creating virtual environment (.venv)...")
        result = subprocess.run(
            f'"{sys.executable}" -m venv "{VENV}"', shell=True
        )
        if result.returncode != 0:
            # Homebrew Python sometimes ships without a working ensurepip.
            # Create without pip, then bootstrap it manually.
            shutil.rmtree(VENV, ignore_errors=True)
            sh(f'"{sys.executable}" -m venv --without-pip "{VENV}"')
            bootstrap_pip()
        print("  Virtual environment ready.")

    banner("Installing Python dependencies...")
    sh(f'"{VENV_PYTHON}" -m pip install -r "{REQ}" -q --upgrade')
    print("  Done.")


def check_tools():
    v = sys.version_info
    if v < (3, 10):
        print("  Python 3.10 or newer is required.")
        sys.exit(1)

    # Homebrew Python 3.13+ on macOS has a libexpat mismatch that breaks pip.
    # The official python.org installer bundles its own libraries and works correctly.
    try:
        import xml.parsers.expat  # noqa — probe for the broken symbol
    except ImportError:
        print(f"\n  Python {v.major}.{v.minor} from Homebrew has a macOS libexpat")
        print("  compatibility issue that breaks pip and venv.")
        print()
        print("  Fix: install the official Python 3.12 from python.org:")
        print("    https://www.python.org/ftp/python/3.12.9/python-3.12.9-macos11.pkg")
        print()
        print("  Then run:  rm -rf .venv && python3.12 start.py")
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
