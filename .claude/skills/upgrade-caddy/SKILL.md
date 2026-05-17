---
name: upgrade-caddy
description: Safely upgrade the Caddy reverse proxy container running on the sswpa GCP VM (ngo-backend). Researches release notes and CVEs between current and target version, runs a validation plan before and after, and auto-rolls back on validation failure. Use when the user wants to upgrade Caddy, check for Caddy security updates, or verify the current Caddy deployment is healthy.
---

Upgrade the Caddy reverse proxy on the production VM safely, with research, validation, and auto-rollback.

## Deployment facts (verify, don't assume)

These are recorded from the deployment as of 2026-05-15. Re-check at step 1 — they may have changed.

- **VM**: `ngo-backend` in zone `us-central1-c`, GCP project `tech-bridge-initiative`
- **SSH user**: `wu_di_network`
- **Container**: `caddy-proxy` on docker network `sswpa-net`
- **Image**: `caddy:latest` from Docker Hub
- **Mounts**:
  - named volume `caddy_data` → `/data` (Let's Encrypt certs — survives `docker rm`)
  - named volume `caddy_config` → `/config`
  - bind `/mnt/stateful_partition/caddy` → `/etc/caddy` (Caddyfile)
- **Ports**: 80/tcp, 443/tcp mapped to host. UDP/443 (HTTP/3) is intentionally NOT mapped — we don't run HTTP/3.
- **Cmd**: `caddy run --config /etc/caddy/Caddyfile --adapter caddyfile`
- **Upstream**: reverse proxies to `sswpa-web:8000` on same docker network
- **Domains served**: `sswpa.org`, `www.sswpa.org`

If gcloud config isn't on `marina` (project `tech-bridge-initiative`), switch first: `gcloud config configurations activate marina`.

## Canonical `docker run` command

This is the authoritative command. Both upgrade and rollback use it, only swapping `${IMAGE}`. If the live container's args drift from this, stop and ask the user before continuing.

```bash
sudo docker run -d \
  --name caddy-proxy \
  --restart unless-stopped \
  --network sswpa-net \
  -p 80:80 -p 443:443 \
  -v caddy_config:/config \
  -v caddy_data:/data \
  -v /mnt/stateful_partition/caddy:/etc/caddy \
  ${IMAGE} \
  caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
```

## Phases

### Phase 1 — Capture current state

Run on the VM and record (you'll need these for research, rollback, and the upgrade log):

```bash
gcloud compute ssh wu_di_network@ngo-backend --zone=us-central1-c --command="
  echo '=== Caddy version ===' &&
  sudo docker exec caddy-proxy caddy version &&
  echo '=== Current image ID ===' &&
  sudo docker inspect caddy-proxy --format '{{.Image}}' &&
  echo '=== Container args (sanity check vs canonical command) ===' &&
  sudo docker inspect caddy-proxy --format 'Cmd: {{.Config.Cmd}}{{println}}Network: {{range \$k, \$_ := .NetworkSettings.Networks}}{{\$k}} {{end}}{{println}}Ports: {{.HostConfig.PortBindings}}{{println}}Mounts:{{println}}{{range .Mounts}}  {{.Type}} {{.Source}} -> {{.Destination}}{{println}}{{end}}'
"
```

**Sanity check**: container args should match the canonical run command above. If they don't (extra/missing volumes, different ports, different cmd), STOP and ask the user — someone may have customized the setup since this skill was written.

**Save** `OLD_VERSION` (e.g. `v2.10.0`) and `OLD_IMAGE_ID` (e.g. `sha256:6ddf...`). These will be reused in Phase 5 (rollback) and Phase 7 (log).

### Phase 2 — Research target version

1. Fetch the Caddy GitHub releases page to find versions newer than `OLD_VERSION`:
   - `WebFetch https://github.com/caddyserver/caddy/releases` — list version numbers and dates
2. For each version between `OLD_VERSION` (exclusive) and latest (inclusive), pull release notes. Focus on:
   - **Security fixes / CVEs** — note CVE IDs and whether the affected feature is used in our Caddyfile (`/mnt/stateful_partition/caddy/Caddyfile`)
   - **Breaking changes** — Caddyfile syntax, default behaviors (especially `reverse_proxy`, headers, TLS)
   - **Default behavior changes** that affect a simple `reverse_proxy + encode + header` config
3. Search the web for "Caddy X.Y.Z CVE" for any version in the range. Cross-reference against the [Caddy security advisories on GitHub](https://github.com/caddyserver/caddy/security/advisories).
4. **Recommend a target version** to the user:
   - Default recommendation: **latest stable patch release** (not a `-rc` or `-beta`).
   - If a major version jump (e.g. v2 → v3) appears, do NOT auto-recommend it; flag it and ask explicitly.
   - Present findings as: which CVEs are fixed, which (if any) affect our config, breaking changes that affect us, and the recommended `TARGET_VERSION`.
5. **Wait for user confirmation** of `TARGET_VERSION` before proceeding. Always pin to a specific version tag (e.g. `caddy:2.11.3`), never `caddy:latest`, so rollback is unambiguous.

### Phase 3 — Pre-upgrade validation (baseline)

Run the validation plan against the **current** deployment. See [validation-plan.md](validation-plan.md).

All checks must pass. If any fail, STOP — the system was broken before we touched it, and the user needs to know.

### Phase 4 — Config compatibility check

Before swapping containers, validate the existing Caddyfile parses cleanly under the new image:

```bash
gcloud compute ssh wu_di_network@ngo-backend --zone=us-central1-c --command="
  sudo docker pull caddy:${TARGET_VERSION} &&
  sudo docker run --rm \
    -v /mnt/stateful_partition/caddy:/etc/caddy:ro \
    caddy:${TARGET_VERSION} \
    caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
"
```

If validation fails (non-zero exit or errors in output): STOP. Show the user the error. Do not proceed — the new version has a breaking Caddyfile change.

### Phase 5 — Perform the upgrade

```bash
gcloud compute ssh wu_di_network@ngo-backend --zone=us-central1-c --command="
  set -e &&
  echo '=== Tagging old image as caddy:rollback for safety ===' &&
  sudo docker tag ${OLD_IMAGE_ID} caddy:rollback &&
  echo '=== Stopping old container ===' &&
  sudo docker stop caddy-proxy &&
  sudo docker rm caddy-proxy &&
  echo '=== Starting new container with caddy:${TARGET_VERSION} ===' &&
  sudo docker run -d \
    --name caddy-proxy \
    --restart unless-stopped \
    --network sswpa-net \
    -p 80:80 -p 443:443 \
    -v caddy_config:/config \
    -v caddy_data:/data \
    -v /mnt/stateful_partition/caddy:/etc/caddy \
    caddy:${TARGET_VERSION} \
    caddy run --config /etc/caddy/Caddyfile --adapter caddyfile &&
  echo '=== Waiting 5s for container to settle ===' &&
  sleep 5 &&
  sudo docker ps --filter name=caddy-proxy --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
"
```

Brief downtime (~5–10s) during the swap is expected; sswpa.org will return connection refused / 502 during that window.

### Phase 6 — Post-upgrade validation (and auto-rollback)

Re-run the validation plan ([validation-plan.md](validation-plan.md)) against the new deployment.

- If **all pass**: proceed to Phase 7.
- If **any fail**: **auto-rollback immediately** without prompting:

  ```bash
  gcloud compute ssh wu_di_network@ngo-backend --zone=us-central1-c --command="
    set -e &&
    echo '=== AUTO-ROLLBACK: validation failed ===' &&
    sudo docker stop caddy-proxy &&
    sudo docker rm caddy-proxy &&
    sudo docker run -d \
      --name caddy-proxy \
      --restart unless-stopped \
      --network sswpa-net \
      -p 80:80 -p 443:443 \
      -v caddy_config:/config \
      -v caddy_data:/data \
      -v /mnt/stateful_partition/caddy:/etc/caddy \
      caddy:rollback \
      caddy run --config /etc/caddy/Caddyfile --adapter caddyfile &&
    sleep 5 &&
    sudo docker ps --filter name=caddy-proxy --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
  "
  ```

  Then re-run validation against the rolled-back container. Report to the user:
  1. Which validation check failed (specific test name + actual output)
  2. That rollback completed
  3. That the rolled-back container passes validation (or doesn't — escalate hard if so)
  4. The new version's release notes for the failing area, so the user can decide next steps

### Phase 7 — Record the upgrade

Append a one-line entry to [upgrade-log.md](upgrade-log.md):

```
- 2026-MM-DD: v2.10.0 (sha256:6ddf…) → v2.11.3 (sha256:abcd…) — fixes CVE-2026-30851, CVE-2026-27590, CVE-2026-27585. No breaking changes affecting our config. Verified.
```

If a rollback happened, log that too:

```
- 2026-MM-DD: ATTEMPTED v2.10.0 → v2.11.4, rolled back. Failure: <which check, what output>. Investigate before retry.
```

## One-time validation-plan establishment

The validation plan in [validation-plan.md](validation-plan.md) was designed once and reused across upgrades. **Re-evaluate the plan when**:
- New domains are added to Caddyfile (need to add cert/SAN checks for them)
- New security headers are added to Caddyfile (need to assert them)
- The upstream app changes (`sswpa-web` → something else)
- A real-world incident reveals a check we should have had

Don't expand the plan on every run — keep it tight and fast.

## Notes

- This skill does NOT upgrade the underlying VM, the `sswpa-web` container, or the Caddyfile itself. Only the Caddy container image.
- Let's Encrypt certs live in the `caddy_data` named volume and survive container `rm`. **Do not** delete or wipe that volume during an upgrade — re-issuance would hit Let's Encrypt rate limits.
- The `caddy:rollback` tag is overwritten on each upgrade (it always means "the version we were just running before this upgrade"). That's intentional — we only need one-step rollback.
- The skill assumes `caddy:latest` will eventually move beyond v2.11.x; always pin `TARGET_VERSION` to a specific tag.
