# Security Policy

**EIDOLON is a local-only research simulator.** It makes no outbound network calls, requires no API keys, and binds its server to `127.0.0.1` by default.

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ Security fixes provided |

## Reporting a vulnerability

Please **do not** disclose a vulnerability in a public issue. Use GitHub's private reporting channel:

1. Open <https://github.com/sahusatya2008/eidolon/security/advisories/new>, or
2. contact the owner privately via GitHub (<https://github.com/sahusatya2008>).

Include the affected file/endpoint, reproduction steps, impact, and any suggested fix. You should receive an acknowledgement within 7 days and a remediation decision within 30 days.

## Hardening in place

- **Local-only CORS:** cross-origin API requests are accepted only from `127.0.0.1`, `localhost` or `[::1]` (override with `EIDOLON_ALLOWED_ORIGINS`).
- **WebSocket origin check:** `/ws/simulation` closes non-loopback browser origins with WebSocket policy code **1008** before sending any state; non-browser clients without an `Origin` header remain supported.
- **Restricted HTTP surface:** only `GET`, `POST`, `PATCH`, `DELETE`, `OPTIONS` and JSON/auth headers are allowed.
- **Path safety:** report downloads sanitise filenames with `Path(filename).name`; no user path reaches the filesystem.
- **Pinned dependencies:** exact versions in `pyproject.toml` and `frontend/package.json`; Dependabot checks both ecosystems weekly.
- **Reproducibility:** snapshots carry a SHA-256 checksum and full RNG state; tampered snapshots are rejected.

## Out of scope

Social engineering, physical access to the host, vulnerabilities in the user's browser/OS, and issues in third-party services. Because the app is intentionally offline and unauthenticated on loopback, anyone with local access to the host can control the simulation — do not expose it to a public network.

© 2026 Satya Narayan Sahu. All rights reserved. See [LICENSE](LICENSE).
