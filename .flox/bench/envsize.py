#!/usr/bin/env python3
"""Closure size of a built Flox environment, as a cold machine would download it.

usage: envsize.py <env-path> [--top N] [--paths-out FILE]

<env-path> is the environment's store path (realpath "$FLOX_ENV" inside an
activation). Looks up every path's .narinfo on cache.nixos.org and
cache.flox.dev and prints the package count, compressed download, unpacked
size, how many paths each cache holds, and the largest downloads with what
references them. --paths-out writes the substitutable paths, one per line
(input for coldfetch.sh).
"""
import argparse, concurrent.futures as cf, subprocess, urllib.request

CACHES = {"nixos": "https://cache.nixos.org", "flox": "https://cache.flox.dev"}

ap = argparse.ArgumentParser()
ap.add_argument("env")
ap.add_argument("--top", type=int, default=12)
ap.add_argument("--paths-out")
a = ap.parse_args()


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.split()


paths = run("nix-store", "-qR", a.env)


def narinfo(cache, p):
    h = p.split("/")[3].split("-")[0]
    try:
        t = urllib.request.urlopen(f"{cache}/{h}.narinfo", timeout=20).read().decode()
        return dict(l.split(": ", 1) for l in t.splitlines() if ": " in l)
    except Exception:
        return None


info = {}
with cf.ThreadPoolExecutor(32) as ex:
    for k, url in CACHES.items():
        info[k] = dict(zip(paths, ex.map(lambda p: narinfo(url, p), paths)))


def best(p):
    return info["nixos"][p] or info["flox"][p]


sub = [p for p in paths if best(p)]
size = lambda p: int(best(p).get("FileSize", 0))
print(f"paths {len(paths)}  substitutable {len(sub)}  local-only {len(paths) - len(sub)}")
print(f"download {sum(map(size, sub)) / 1e6:.0f} MB  "
      f"unpacked {sum(int(best(p)['NarSize']) for p in sub) / 1e9:.2f} GB")
nx = sum(1 for p in paths if info["nixos"][p])
fx = sum(1 for p in paths if info["flox"][p])
fo = sum(1 for p in paths if info["flox"][p] and not info["nixos"][p])
print(f"cache.nixos.org holds {nx}, cache.flox.dev holds {fx} ({fo} only there)")

refs = {}
for p in paths:
    for r in run("nix-store", "-q", "--references", p):
        if r != p:
            refs.setdefault(r, []).append(p)
name = lambda p: p.split("-", 1)[1]
print("largest downloads (<- referenced by):")
for p in sorted(sub, key=lambda p: -size(p))[: a.top]:
    by = ", ".join(sorted(name(x) for x in refs.get(p, []))[:5])
    print(f"  {size(p) / 1e6:6.1f} MB  {name(p):34s} <- {by}")

if a.paths_out:
    with open(a.paths_out, "w") as f:
        f.write("\n".join(sub) + "\n")
