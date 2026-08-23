import subprocess
import sys


def main():
    """Run pytest suite."""
    cmd = [sys.executable, "-m", "pytest", "-v"]
    print("Executing pytest test suite...")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
