# Test 1: Does sqlparse.parse("") return empty tuple?
import sqlparse
r = sqlparse.parse("")
print(f"parse('') = {repr(r)}, len={len(r)}")

# Test 2: Does sqlparse.parse("  ") return empty tuple?
r2 = sqlparse.parse("  ")
print(f"parse('  ') = {repr(r2)}, len={len(r2)}")

# Test 3: What Python version + can asyncio.run() work inside a running loop?
import sys
print(f"Python {sys.version}")

import asyncio
async def test():
    try:
        asyncio.run(asyncio.sleep(0))
        print("asyncio.run() inside loop: WORKS")
    except RuntimeError as e:
        print(f"asyncio.run() inside loop: FAILS ({e})")
asyncio.run(test())
