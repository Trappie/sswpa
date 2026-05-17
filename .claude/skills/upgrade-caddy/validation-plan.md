# Caddy upgrade validation plan

Used by [SKILL.md](SKILL.md) in Phase 3 (baseline) and Phase 6 (post-upgrade). Every check must pass — any failure aborts the upgrade or triggers rollback.

Run all checks. Report per-check pass/fail with the actual output captured. Do not gloss over warnings.

## C1. HTTPS smoke test (both domains, both protocols)

```bash
for url in https://sswpa.org https://www.sswpa.org https://sswpa.org/health; do
  echo "--- $url ---"
  curl -sS -o /dev/null -w 'http_code=%{http_code} time_total=%{time_total}s\n' "$url"
done
echo "--- http→https redirect ---"
curl -sS -o /dev/null -w 'http_code=%{http_code} location=%{redirect_url}\n' http://sswpa.org
```

**Pass criteria**:
- `https://sswpa.org` → `http_code=200`
- `https://www.sswpa.org` → `http_code=200`
- `https://sswpa.org/health` → `http_code=200` (response body should be `{"status":"healthy"}` or similar — also fetch and confirm it's not an HTML error page)
- `http://sswpa.org` → `http_code` in `301`/`302`/`308` with `location` starting `https://`
- All response times < 3s

## C2. TLS certificate validity

Caddy issues a separate certificate per site address by default, so we check each domain independently. Each cert covers only its own name (not a combined SAN).

```bash
for host in sswpa.org www.sswpa.org; do
  echo "--- $host ---"
  echo | openssl s_client -servername "$host" -connect "$host":443 2>/dev/null \
    | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
done
```

**Pass criteria** (apply to both `sswpa.org` and `www.sswpa.org`):
- Issuer organization is `Let's Encrypt` (intermediate CN may be any of `E5`/`E7`/`E8`/`R10`/`R11`/etc.)
- `notAfter` is at least 7 days in the future
- SAN list contains `DNS:<that-host>` (so sswpa.org cert has `DNS:sswpa.org`, www.sswpa.org cert has `DNS:www.sswpa.org`)
- Subject CN matches the host

## C3. Security headers

```bash
curl -sSI https://sswpa.org | tr -d '\r'
```

**Pass criteria** (case-insensitive header match):
- `Strict-Transport-Security: max-age=31536000` (or larger)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

If Caddyfile changes later (new headers added or values updated), update this list accordingly.

## C4. Container health

```bash
gcloud compute ssh wu_di_network@ngo-backend --zone=us-central1-c --command="
  echo '=== docker ps ===' &&
  sudo docker ps --format 'table {{.Names}}\t{{.Status}}' &&
  echo '=== caddy-proxy last 50 log lines ===' &&
  sudo docker logs --tail 50 caddy-proxy 2>&1 &&
  echo '=== sswpa-web last 50 log lines ===' &&
  sudo docker logs --tail 50 sswpa-web 2>&1
"
```

**Pass criteria**:
- Both `caddy-proxy` and `sswpa-web` show `Up` (not `Restarting`, not `Exited`)
- For `sswpa-web`: `Status` includes `(healthy)` (Dockerfile has a HEALTHCHECK)
- `caddy-proxy` logs: no `ERROR`, no `panic`, no `failed to obtain certificate`, no `dial tcp ... refused` *for the upstream* in the last 50 lines. Lines mentioning routine cert renewal or HTTP/3 negotiation are fine.
- `sswpa-web` logs: no `Traceback`, no `Internal Server Error`, no `ERROR` in the last 50 lines.

**Exception**: immediately after the upgrade (Phase 6), the last few caddy log lines will show shutdown/startup messages. Those are expected. Look at lines from after the most recent `serving initial configuration` line.

## Summary format to report

After running all checks, report like this:

```
Validation results (pre-upgrade / post-upgrade):
  C1 HTTPS smoke test:      PASS / FAIL (details: ...)
  C2 TLS certificate:       PASS / FAIL (notAfter: 2026-08-13, issuer: Let's Encrypt R10)
  C3 Security headers:      PASS / FAIL (missing: ...)
  C4 Container health:      PASS / FAIL (caddy log line N: "ERROR ...")
```

If any of C1–C4 are FAIL, abort upgrade (Phase 3) or auto-rollback (Phase 6).

> **Note**: HTTP/3 / UDP/443 is intentionally NOT mapped on the host. If sswpa.org ever decides to enable HTTP/3, this validation plan will need a C5 check added back in.
