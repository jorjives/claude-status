# .deb Packaging and CI Release Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a .deb package for claude-status via GitHub Actions, with edge (pre-release) and versioned (latest) release channels, plus a local pre-push hook for test enforcement.

**Architecture:** A `debian/` directory in the repo holds the control file, maintainer scripts, and systemd unit. The GitHub Actions workflow assembles these into a dpkg-deb build directory, injects the version, and publishes to GitHub Releases. A `.githooks/pre-push` script runs tests locally before any push.

**Tech Stack:** dpkg-deb, GitHub Actions, bash, systemd

**Spec:** `docs/superpowers/specs/2026-03-18-deb-packaging-and-ci-design.md`

---

## File Structure

### New files

| File | Responsibility |
|---|---|
| `debian/control` | Package metadata and dependencies (version placeholder) |
| `debian/postinst` | Post-install: pip install Python deps |
| `debian/prerm` | Pre-remove: best-effort stop service for active users |
| `debian/claude-status.service` | systemd user unit |
| `.github/workflows/release.yml` | CI: build .deb and publish GitHub release |
| `.githooks/pre-push` | Local hook: run tests before push |

### Modified files

| File | Change |
|---|---|
| `install.sh` | Add `git config core.hooksPath .githooks` |
| `README.md` | Add .deb install section and development setup |

---

### Task 1: Pre-push hook

**Files:**
- Create: `.githooks/pre-push`
- Modify: `install.sh`

- [ ] **Step 1: Create the pre-push hook**

```bash
#!/usr/bin/env bash
set -euo pipefail
echo "Running tests before push..."
PYSTRAY_BACKEND=xorg python3 -m pytest tests/ -v
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x .githooks/pre-push`

- [ ] **Step 3: Activate the hooks path**

Run: `git config core.hooksPath .githooks`

- [ ] **Step 4: Add hooks setup to install.sh**

Add after the GNOME check block, before the final `echo "Done."`:

```bash
# Developer setup: enable git hooks
if [ -d "$SCRIPT_DIR/.git" ]; then
    git -C "$SCRIPT_DIR" config core.hooksPath .githooks
    echo "Git hooks enabled."
fi
```

- [ ] **Step 5: Verify the hook works**

Run: `git stash && git push --dry-run 2>&1 || true && git stash pop`

The hook should run tests and show 9 passed.

- [ ] **Step 6: Commit**

```bash
git add .githooks/pre-push install.sh
git commit -m "Add pre-push hook to run tests before push"
```

---

### Task 2: Debian package files

**Files:**
- Create: `debian/control`
- Create: `debian/postinst`
- Create: `debian/prerm`
- Create: `debian/claude-status.service`

- [ ] **Step 1: Create the control file**

Create `debian/control`:

```
Package: claude-status
Version: VERSION
Architecture: all
Maintainer: jorjives
Depends: python3, python3-pip, gir1.2-ayatanaappindicator3-0.1
Description: System tray icon showing Claude API status
 Polls status.claude.com every 60 seconds and displays a colour-coded
 tray icon: green for operational, orange for minor incidents, red for
 major/critical incidents or when status is unavailable.
```

`VERSION` is a placeholder — the CI workflow substitutes it at build time.

- [ ] **Step 2: Create the postinst script**

Create `debian/postinst`:

```bash
#!/usr/bin/env bash
set -e
pip3 install --break-system-packages -r /usr/share/claude-status/requirements.txt
```

- [ ] **Step 3: Make postinst executable**

Run: `chmod +x debian/postinst`

- [ ] **Step 4: Create the prerm script**

Create `debian/prerm`:

```bash
#!/usr/bin/env bash
set -e
# Best-effort stop for all logged-in users
for uid in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $1}'); do
    systemctl --user -M "$uid@" stop claude-status 2>/dev/null || true
done
```

- [ ] **Step 5: Make prerm executable**

Run: `chmod +x debian/prerm`

- [ ] **Step 6: Create the systemd unit**

Create `debian/claude-status.service`:

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

- [ ] **Step 7: Verify the debian directory**

Run: `ls -la debian/`

Expected: `control`, `postinst` (executable), `prerm` (executable), `claude-status.service`

- [ ] **Step 8: Commit**

```bash
git add debian/
git commit -m "Add debian package files (control, postinst, prerm, systemd unit)"
```

---

### Task 3: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Create the workflow file**

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    branches: [master]
    tags: ["v*"]

permissions:
  contents: write

jobs:
  build-deb:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Determine version
        id: version
        run: |
          if [[ "$GITHUB_REF" == refs/tags/v* ]]; then
            echo "version=${GITHUB_REF#refs/tags/v}" >> "$GITHUB_OUTPUT"
            echo "release_name=${GITHUB_REF#refs/tags/}" >> "$GITHUB_OUTPUT"
            echo "prerelease=false" >> "$GITHUB_OUTPUT"
          else
            echo "version=0.0.0~edge" >> "$GITHUB_OUTPUT"
            echo "release_name=edge" >> "$GITHUB_OUTPUT"
            echo "prerelease=true" >> "$GITHUB_OUTPUT"
          fi

      - name: Build .deb
        run: |
          PKG="claude-status_${{ steps.version.outputs.version }}_all"
          mkdir -p "$PKG/DEBIAN"
          mkdir -p "$PKG/usr/share/claude-status"
          mkdir -p "$PKG/usr/lib/systemd/user/graphical-session.target.wants"

          # Control file with version substituted
          sed "s/^Version: VERSION$/Version: ${{ steps.version.outputs.version }}/" \
            debian/control > "$PKG/DEBIAN/control"

          # Maintainer scripts
          cp debian/postinst "$PKG/DEBIAN/postinst"
          cp debian/prerm "$PKG/DEBIAN/prerm"

          # App files
          cp tray.py "$PKG/usr/share/claude-status/tray.py"
          cp requirements.txt "$PKG/usr/share/claude-status/requirements.txt"

          # systemd unit + auto-start symlink
          cp debian/claude-status.service "$PKG/usr/lib/systemd/user/claude-status.service"
          ln -s ../claude-status.service \
            "$PKG/usr/lib/systemd/user/graphical-session.target.wants/claude-status.service"

          dpkg-deb --build "$PKG"

      - name: Delete existing edge release and tag
        if: steps.version.outputs.prerelease == 'true'
        run: |
          gh release delete edge --yes --cleanup-tag 2>/dev/null || true
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Create edge release
        if: steps.version.outputs.prerelease == 'true'
        run: |
          gh release create edge \
            claude-status_${{ steps.version.outputs.version }}_all.deb \
            --title "edge" \
            --prerelease \
            --notes "Built from master at $(git rev-parse --short HEAD)"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Create versioned release
        if: steps.version.outputs.prerelease == 'false'
        run: |
          gh release create "${{ steps.version.outputs.release_name }}" \
            claude-status_${{ steps.version.outputs.version }}_all.deb \
            --title "${{ steps.version.outputs.release_name }}" \
            --latest \
            --generate-notes
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))" 2>&1 || echo "Install PyYAML or check syntax manually"`

If PyYAML isn't installed, visually confirm indentation is correct.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "Add GitHub Actions workflow for .deb release pipeline"
```

---

### Task 4: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add .deb install section after the existing Install section**

After the current "Install" section and before "Uninstall", add:

```markdown
## Install from .deb

Download the latest `.deb` from [GitHub Releases](https://github.com/jorjives/claude-status/releases/latest):

```bash
sudo apt install ./claude-status_*_all.deb
```

The service starts automatically on your next login. To start it immediately:

```bash
systemctl --user start claude-status
```
```

- [ ] **Step 2: Update the Uninstall section to cover both methods**

Replace the Uninstall section with:

```markdown
## Uninstall

If installed via .deb:

```bash
sudo apt remove claude-status
```

If installed via install.sh:

```bash
systemctl --user disable --now claude-status
rm ~/.config/systemd/user/claude-status.service
systemctl --user daemon-reload
```
```

- [ ] **Step 3: Add development section before "Running tests"**

Before the "Running tests" section, add:

```markdown
## Development

After cloning, set up git hooks:

```bash
git config core.hooksPath .githooks
```

This runs tests automatically before each push.
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "Update README with .deb install and development setup"
```

---

### Task 5: Push and verify

- [ ] **Step 1: Push to master**

Run: `git push`

The pre-push hook should run tests (9 passed), then the push proceeds.

- [ ] **Step 2: Verify the GitHub Actions workflow runs**

Run: `gh run list --limit 1`

Wait for it to complete:

Run: `gh run watch`

- [ ] **Step 3: Verify the edge release was created**

Run: `gh release view edge`

Expected: a pre-release named "edge" with a `claude-status_0.0.0~edge_all.deb` asset.

- [ ] **Step 4: Download and inspect the .deb**

Run: `gh release download edge --dir /tmp/deb-test && dpkg-deb --info /tmp/deb-test/claude-status_0.0.0~edge_all.deb`

Verify: package name, version, architecture (all), and dependencies are correct.

- [ ] **Step 5: Commit any fixes if needed, otherwise done**
