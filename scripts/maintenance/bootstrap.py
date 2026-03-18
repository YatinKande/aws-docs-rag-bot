import asyncio
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.services.retrieval.bootstrap_sync import bootstrap_sync

async def main():
    print("🚀 Starting Manual Bootstrap Sync...")
    try:
        await bootstrap_sync.run_bootstrap_sync()
        print("✨ Manual Bootstrap Sync Complete!")
    except KeyboardInterrupt:
        print("\n🛑 Bootstrap interrupted.")
    except Exception as e:
        print(f"❌ Bootstrap failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
