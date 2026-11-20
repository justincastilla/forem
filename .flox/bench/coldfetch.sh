#!/usr/bin/env bash
# Time a cold download: substitute every path in <pathsfile> into a brand-new,
# empty Nix store (no daemon, so --option flags apply), then delete that store.
#
#   COLD_ROOT=/some/scratch/dir coldfetch.sh <label> <pathsfile> [--option k v ...]
#
# Examples:
#   coldfetch.sh default paths-aarch64-darwin.txt
#   coldfetch.sh http1   paths-aarch64-darwin.txt --option http2 false
#   coldfetch.sh flox    paths-aarch64-darwin.txt --option extra-substituters https://cache.flox.dev
set -u
label=$1 list=$2
shift 2
root=$(mktemp -d "${COLD_ROOT:?set COLD_ROOT to a scratch directory}/run.XXXX")
now() { python3 -c 'import time; print(time.time())'; }
start=$(now)
xargs nix-store --store "local?root=$root" \
  --option narinfo-cache-negative-ttl 0 --option narinfo-cache-positive-ttl 0 \
  "$@" --realise < "$list" >/dev/null 2>"$root.err"
rc=$?
end=$(now)
mb=$(du -sm "$root/nix/store" | cut -f1)
printf '%-24s rc=%s %6.1f s  unpacked %5s MB  %s\n' \
  "$label" "$rc" "$(echo "$end - $start" | bc)" "$mb" "$*"
[ $rc -ne 0 ] && tail -3 "$root.err"
# The throwaway store is read-only once realised; make it writable to remove it.
chmod -R u+w "$root" 2>/dev/null
find "$root" -delete 2>/dev/null
rm -f "$root.err"
