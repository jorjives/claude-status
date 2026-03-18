# .deb Packaging and CI Release Pipeline

## Goal

Distribute claude-status as a `.deb` package built automatically by GitHub Actions, with two release channels:

- **edge** — rebuilt on every push to `master`, always reflects HEAD, marked as pre-release
- **vX.Y.Z** — created on version tag push, marked as GitHub's `latest` release

## .deb Package

### Installed files

| Source | Destination |
|---|---|
| `tray.py` | `/usr/share/claude-status/tray.py` |
| `requirements.txt` | `/usr/share/claude-status/requirements.txt` |
| systemd unit | `/usr/lib/systemd/user/claude-status.service` |
| symlink | `/usr/lib/systemd/user/graphical-session.target.wants/claude-status.service` |

### Control file

- **Package:** `claude-status`
- **Architecture:** `all` (pure Python, no compiled code)
- **Depends:** `python3, python3-pip, gir1.2-ayatanaappindicator3-0.1`
- **Description:** System tray icon showing Claude API status

Version is injected at build time: the tag version for tagged releases, `0.0.0~edge` for edge builds.

### Maintainer scripts

- **postinst:** Runs `pip3 install --break-system-packages -r /usr/share/claude-status/requirements.txt` to install pystray and Pillow.
- **prerm:** Runs a best-effort stop of the claude-status user service for all active user sessions.

### systemd unit

```ini
[Unit]
Description=Claude Status System Tray Icon
After=graphical-session.target

[Service]
ExecStart=/usr/bin/python3 /usr/share/claude-status/tray.py
Restart=on-failure

[Install]
WantedBy=graphical-session.target
```

Installed to `/usr/lib/systemd/user/` (system-wide user unit), making it available to all users. The .deb also ships a symlink at `/usr/lib/systemd/user/graphical-session.target.wants/claude-status.service` so the service auto-starts on login without each user needing to run `systemctl --user enable`.

## GitHub Actions Workflow

**File:** `.github/workflows/release.yml`

**Triggers:**
- `push` to `master`
- `push` of tags matching `v*`

**Steps:**

1. Checkout repo
2. Determine version: strip `v` prefix from tag (e.g. `v1.2.0` becomes `1.2.0`), or use `0.0.0~edge` for master pushes
3. Build `.deb` directory layout in a temp directory, substituting version into the control file
4. Run `dpkg-deb --build` to produce `claude-status_<version>_all.deb`
5. Create/update GitHub release:
   - **Master push:** create or update a release named `edge`, marked as pre-release, overwriting the previous `.deb` asset
   - **Tag push:** create a new release named after the tag, marked as `latest`

**No test step** — tests require a display server. Enforced locally via pre-push hook instead.

## Pre-push Hook

**File:** `.githooks/pre-push`

Runs `PYSTRAY_BACKEND=xorg python3 -m pytest tests/ -v` before allowing a push. Blocks the push if any test fails.

Activated by running `git config core.hooksPath .githooks`. The `install.sh` script and README instruct users to do this.

## Changes to Existing Files

- **`install.sh`:** Add `git config core.hooksPath .githooks` for developer setup.
- **`README.md`:** Add sections for .deb installation (`sudo apt install ./claude-status_*.deb`) and development setup (hooks).
- **`.gitignore`:** No changes needed (build output stays in CI, not committed).

## What stays the same

- `install.sh` remains the primary install path for people cloning the repo
- `tray.py`, `tests/`, and `requirements.txt` are unchanged
- No new Python dependencies
