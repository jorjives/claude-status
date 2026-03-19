# App Icon

## Goal

Replace the hand-drawn Pillow "A" tray icon with the real Claude sparkle logo, and add a static icon for desktop entry and repo identity.

## Visual treatment

White Claude sparkle on a coloured circle background. The SVG path from `claude-color.svg` is used as the logo shape.

### Tray icon (dynamic)

Replace `make_image()` in `tray.py`. Instead of drawing polygons for an "A", render the Claude SVG path as a white fill on a coloured circle. The SVG path data is embedded directly in the Python source. Colour changes based on status:

- Green (#4CAF50) — operational
- Orange (#FF9800) — minor incident
- Red (#F44336) — major/critical/error

Size remains 64x64. Approach: pre-render the Claude sparkle SVG to a white-on-transparent PNG at 64x64, embed it as base64 in `tray.py`, and composite it onto the coloured circle at runtime. This avoids SVG path parsing entirely and ensures pixel-perfect rendering. No new dependencies required — Pillow handles PNG decoding and compositing.

### Static icon

A single SVG file at `icons/claude-status.svg` — the Claude sparkle in white on a Claude orange (#D97757) circle. Used for:

- Desktop entry icon
- README / repo identity
- Installed to `/usr/share/icons/hicolor/scalable/apps/claude-status.svg` via `.deb`

### Desktop entry

`claude-status.desktop` conforming to the freedesktop Desktop Entry spec:

```ini
[Desktop Entry]
Type=Application
Name=Claude Status
Comment=System tray icon showing Claude API status
Exec=/usr/bin/python3 /usr/share/claude-status/tray.py
Icon=claude-status
Terminal=false
Categories=Utility;
```

Installed to:
- `.deb`: `/usr/share/applications/claude-status.desktop`
- `install.sh`: `~/.local/share/applications/claude-status.desktop`

## File changes

### New files

| File | Purpose |
|---|---|
| `icons/claude-status.svg` | Static icon (white sparkle on orange circle) |
| `claude-status.desktop` | Desktop entry |

### Modified files

| File | Change |
|---|---|
| `tray.py` | Replace `make_image()` to draw Claude sparkle instead of "A" |
| `debian/control` | No change needed (no new system dependencies) |
| `debian/postinst` | No change needed |
| `.github/workflows/release.yml` | Add icon and .desktop to .deb build |
| `Makefile` | Add icon and .desktop to local build |
| `install.sh` | Install .desktop file and icon for dev users |
| `README.md` | Add icon to the top of the README |

## SVG source

The Claude sparkle SVG path data comes from the user-provided file at `/home/jorjives/Downloads/claude-color.svg`. The path `d` attribute contains the full logo shape. This is used to:

1. Create the static `icons/claude-status.svg` (white sparkle on orange circle)
2. Pre-render a 64x64 white-on-transparent PNG, base64-encoded and embedded in `tray.py` for the dynamic tray icon

## .deb build additions

The CI workflow and Makefile build steps need to copy these additional files into the package:

- `icons/claude-status.svg` → `$PKG/usr/share/icons/hicolor/scalable/apps/claude-status.svg`
- `claude-status.desktop` → `$PKG/usr/share/applications/claude-status.desktop`

## install.sh additions

For dev users (not installing via .deb):

- Copy `claude-status.desktop` to `~/.local/share/applications/`
- Copy `icons/claude-status.svg` to `~/.local/share/icons/hicolor/scalable/apps/`

## Dependencies

No new dependencies. Pillow handles PNG decoding and compositing for the tray icon. The static SVG is hand-crafted.

## What stays the same

- Polling logic, status URL, colour mapping unchanged
- systemd service unchanged
- Pre-push hook unchanged
- Test structure unchanged (tests for colour constants still valid; `make_image` tests will need updating for new output)
