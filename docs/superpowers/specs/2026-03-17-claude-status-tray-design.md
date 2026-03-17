# Claude Status Systray Icon — Design Spec

**Date:** 2026-03-17
**Status:** Approved

## Overview

A Linux system tray icon that polls the Claude status API and colors itself green, orange, or red to reflect the current incident status. Built with Python, pystray, and Pillow.

## Architecture

A single Python script (`tray.py`) with no submodules. Dependencies managed via `requirements.txt`. A systemd user service handles autostart.

### Files

```
claude-status/
├── tray.py               # Main script
├── requirements.txt      # pystray, Pillow
├── install.sh            # Install deps and enable systemd service
└── claude-status.service # Systemd user service unit
```

## Status API

Endpoint: `https://status.claude.com/api/v2/status.json`

Response shape:
```json
{"status": {"indicator": "none", "description": "All Systems Operational"}}
```

Indicator values and their colors:
| `indicator` | Color   | Hex       |
|-------------|---------|-----------|
| `none`      | Green   | `#4CAF50` |
| `minor`     | Orange  | `#FF9800` |
| `major`     | Red     | `#F44336` |
| `critical`  | Red     | `#F44336` |

## Icon Design

64×64 PIL image:
- Filled circle in status color (no border)
- White Anthropic "A" drawn with PIL polygon primitives — upward-pointing triangle with a horizontal crossbar cutout
- No external font or image files required

## Polling

- Interval: 60 seconds
- First fetch on startup (no initial delay)
- On error (network failure, non-200 response, parse error): icon turns red, tooltip shows "Status unavailable"
- No backoff — retries on the next 60-second tick
- Thread-safe: background thread writes to a shared variable; main thread reads it to redraw

## Interaction

- Tooltip: the `description` string from the API (e.g. "All Systems Operational")
- Right-click menu:
  - "Open status page" → opens `https://status.claude.com` in the default browser
  - "Quit" → exits the process

## Autostart

Systemd user service at `~/.config/systemd/user/claude-status.service`:
- `Restart=on-failure`
- Runs `python3 /path/to/tray.py`

`install.sh`:
1. `pip install --user -r requirements.txt`
2. Copies `claude-status.service` to `~/.config/systemd/user/`
3. `systemctl --user enable --now claude-status`

## GNOME/Wayland Note

On GNOME/Wayland, the **AppIndicator and KStatusNotifierItem Support** GNOME Shell extension is required for tray icons to appear. The install script will print a reminder if GNOME is detected and the extension is not installed.
