#!/usr/bin/env python3
"""Why is a package in the closure? Prints the shortest chain from each
installed manifest output to every closure path whose name matches.

usage: why.py <env-path> <manifest.lock> <system> <regex>...
example:
  why.py "$(realpath "$FLOX_ENV")" .flox/env/manifest.lock aarch64-darwin '^bootstrap-tools$'
"""
import collections, json, re, subprocess, sys

env, lock, system = sys.argv[1:4]
pats = sys.argv[4:]
q = lambda *c: subprocess.run(c, capture_output=True, text=True, check=True).stdout.split()
paths = q("nix-store", "-qR", env)
refs = {p: [r for r in q("nix-store", "-q", "--references", p) if r != p] for p in paths}
roots = {sp: f'{pk["install_id"]}.{o}'
         for pk in json.load(open(lock))["packages"] if pk["system"] == system
         for o, sp in pk["outputs"].items() if sp in refs}
name = lambda p: p.split("-", 1)[1]

for pat in pats:
    for t in (p for p in paths if re.search(pat, name(p))):
        chains = []
        for root, label in roots.items():
            prev = {root: None}
            dq = collections.deque([root])
            while dq and t not in prev:
                x = dq.popleft()
                for y in refs[x]:
                    if y not in prev:
                        prev[y] = x
                        dq.append(y)
            if t in prev:
                ch, x = [], t
                while x:
                    ch.append(name(x))
                    x = prev[x]
                chains.append((len(ch), label, " -> ".join(reversed(ch))))
        for _, label, chain in sorted(chains)[:4]:
            print(f"{name(t)}: [{label}] {chain}")
