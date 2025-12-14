import sys
import subprocess
from pathlib import Path

def main():
    """
    Shim script to forward commands to python/devbase.py
    """
    root = Path(__file__).parent.resolve()
    target = root / "python" / "devbase.py"
    
    if not target.exists():
        print(f"Error: Could not find {target}")
        sys.exit(1)
        
    try:
        # Forward execution to the real script
        result = subprocess.run(
            [sys.executable, str(target)] + sys.argv[1:],
            check=False  # We handle return code manually
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error launching DevBase: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
