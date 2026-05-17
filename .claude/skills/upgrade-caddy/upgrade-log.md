# Caddy upgrade log

Append-only record of past upgrades. The `upgrade-caddy` skill writes here in Phase 7.

Format per entry:
```
- YYYY-MM-DD: vX.Y.Z (sha256:...) → vA.B.C (sha256:...) — short notes (CVEs fixed, breaking changes, anything weird). Verified.
```

For aborts/rollbacks:
```
- YYYY-MM-DD: ATTEMPTED vX.Y.Z → vA.B.C, rolled back. Failure: <check name + actual output>. Investigate before retry.
```

## History

<!-- Entries below, newest first -->

- 2026-05-15: v2.10.0 (sha256:6ddf74df…) → v2.11.3 (sha256:ec18ee54…) — 13 months of bug fixes + CVE coverage for forward_auth, fastcgi, admin API, file matcher, mTLS, MatchPath/MatchHost. None of the fixed CVEs reachable in our config; upgrade is defense-in-depth. No breaking changes affected our Caddyfile. Side-notes: (1) v2.11.3 emits `alt-svc: h3=":443"` advertising HTTP/3, but UDP/443 is not host-mapped so clients fall back to h2 — harmless. (2) Caddyfile formatting warning still present, run `caddy fmt --overwrite` separately if cosmetic cleanup desired. Verified.
- (Baseline: v2.10.0, sha256:6ddf74dfb6187e856dab57d2bf87ab6ae10f093dd7ced7ec1f6d485eff7e7649, recorded 2026-05-15.)
