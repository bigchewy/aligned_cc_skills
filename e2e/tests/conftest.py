# e2e/tests/conftest.py
import sys
from pathlib import Path

# Add e2e/ to Python path so `from scorers.distinctness import ...` works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
