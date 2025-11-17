"""Dashboard CLI entry point."""

import sys
from pathlib import Path

# Add workflows to path so we can import from it
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.dashboard.dashboard_manager import main

if __name__ == "__main__":
    main()
