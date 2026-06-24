import asyncio
import os
import sys
import traceback

# Inject project root into sys.path to resolve 'backend' module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db.migrations import init_db

if __name__ == "__main__":
    try:
        asyncio.run(init_db())
        print("Migration complete")
    except Exception:
        traceback.print_exc()
