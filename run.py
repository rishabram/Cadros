#!/usr/bin/env python3
"""Entry point: python run.py [--parcel ...]  (uses the project venv python)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prototype.__main__ import main

if __name__ == "__main__":
    main()
