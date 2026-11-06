# tools/measure.py
"""Sends 1,000 searches to the running app, one after another, and prints how long they took
and what they cost: the difference of GET /stats before and after.

python tools/measure.py                         -> 12-14 Nov
python tools/measure.py 2026-12-31 2027-01-02   -> other dates
"""
import http.client
import json
import math
import sys
import time

SEARCHES = 1000
NAMES = ("searches", "databaseQueries", "cacheHits", "cacheMisses")

check_in, check_out = sys.argv[1:3] if len(sys.argv) >= 3 else ("2026-11-12", "2026-11-14")
connection = http.client.HTTPConnection("localhost", 5080)  # one connection for every request


def get(path: str) -> str:
    connection.request("GET", path)
    response = connection.getresponse()
    body = response.read().decode("utf-8")
    if response.status != 200:
        sys.exit(f"GET {path} answered {response.status}: {body}")
    return body


before = json.loads(get("/stats"))
times = []
started = time.perf_counter()
for _ in range(SEARCHES):
    start = time.perf_counter()
    get(f"/rooms/availability?checkIn={check_in}&checkOut={check_out}")
    times.append((time.perf_counter() - start) * 1000)
total = time.perf_counter() - started
after = json.loads(get("/stats"))

times.sort()
p95 = times[math.ceil(0.95 * SEARCHES) - 1]  # 950 of the 1,000 searches were this fast or faster
difference = ",".join(f'"{name}":{after[name] - before[name]}' for name in NAMES)
print(f"{SEARCHES} searches for {check_in} to {check_out}")
print(f"Average: {sum(times) / SEARCHES:.1f} ms")
print(f"p95: {p95:.1f} ms")
print(f"Total: {total:.1f} s")
print(f"GET /stats difference: {{{difference}}}")