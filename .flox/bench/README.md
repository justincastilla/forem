# Flox environment measurements

These scripts measure how much a cold machine downloads to build this
environment, why each large package is there, and how long the download
takes. None of them is used by the environment itself. They need `nix-store`
and Python 3 on the PATH.

| File | What it does |
|---|---|
| `envsize.py` | Package count, compressed download and unpacked size of a built environment, plus how many paths cache.nixos.org and cache.flox.dev each hold |
| `why.py` | The shortest chain from a manifest output to any package in the closure |
| `coldfetch.sh` | Times a download of a path list into a new, empty Nix store |
| `paths-aarch64-darwin.txt` | The 166 downloadable paths for aarch64-darwin, from `manifest.lock` at the commit that added this file |

## Usage

```bash
env=$(flox activate -c 'realpath "$FLOX_ENV"')

# Size, cache coverage, largest downloads; write the path list
python3 .flox/bench/envsize.py "$env" --paths-out /tmp/paths.txt

# Why is bootstrap-tools in the macOS closure?
python3 .flox/bench/why.py "$env" .flox/env/manifest.lock aarch64-darwin '^bootstrap-tools$'

# Cold download into an empty store, with different settings
export COLD_ROOT=$(mktemp -d)
.flox/bench/coldfetch.sh flox-active .flox/bench/paths-aarch64-darwin.txt \
  --option extra-substituters https://cache.flox.dev
.flox/bench/coldfetch.sh http1 .flox/bench/paths-aarch64-darwin.txt \
  --option extra-substituters https://cache.flox.dev --option http2 false
```

`coldfetch.sh` uses `--store local?root=...`, so it substitutes inside the
client without the daemon, and `--option` flags take effect. The default
system configuration lists cache.flox.dev only as a trusted substituter, not
an active one. Without the `extra-substituters` option, the four Flox-built
paths (`flox-interpreter`, `flox-activations`, `bash-envtrace`,
`nss-cacert`) can't be fetched and the run fails.

## Results so far (aarch64-darwin)

| Environment | Packages | Download | Cold download, fast link |
|---|---:|---:|---:|
| This manifest before 20 Nov | 257 | 621 MB | 34 s |
| This manifest | 168 | 285 MB | 18 s |
