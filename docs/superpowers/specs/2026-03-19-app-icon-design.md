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

Size remains 64x64. Pillow's `ImageDraw` can draw arbitrary paths via polygon approximation of the SVG path, or use `cairosvg` / manual path parsing. The simplest approach: parse the SVG path `d` attribute into coordinate pairs and draw them as a filled polygon on the Pillow image.

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

## Dependencies

Pillow's `ImageDraw.polygon()` can render the Claude sparkle path if we convert the SVG path data to a list of (x, y) tuples. The SVG path uses cubic bezier curves (`C` commands) and lines (`l`, `L`), which need to be approximated as line segments for Pillow. This can be done with a small path parser function — no new dependencies required.

Alternatively, if the path approximation is too complex or lossy at 64px, we can pre-render the SVG to a 64x64 PNG and embed it as base64 in the source, compositing it onto the coloured circle. This avoids path parsing entirely.

## What stays the same

- Polling logic, status URL, colour mapping unchanged
- systemd service unchanged
- Pre-push hook unchanged
- Test structure unchanged (tests for colour constants still valid; `make_image` tests will need updating for new output)
