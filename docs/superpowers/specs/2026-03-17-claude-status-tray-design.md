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
- White Anthropic "A": draw a white filled upward-pointing triangle, then draw a white-filled rectangle over it to simulate the crossbar. A simplified approximation is acceptable — exact proportions are unimportant at tray scale (~22×22 px after system scaling)
- No external font or image files required

## Polling

- Interval: 60 seconds
- First fetch on startup (no initial delay)
- On error (network failure, non-200 response, parse error): icon turns red, tooltip shows "Status unavailable"
- No backoff — retries on the next 60-second tick
- Thread-safe: a bare global is sufficient (the GIL provides adequate safety for a single variable assignment). The background thread calls `icon.icon = new_image` and `icon.title = new_tooltip` directly — pystray's property assignments are thread-safe

## Interaction

- Tooltip: the `description` string from the API (e.g. "All Systems Operational")
- Right-click menu:
  - "Open status page" → opens `https://status.claude.com` in the default browser
  - "Quit" → exits the process

## Autostart

Systemd user service at `~/.config/systemd/user/claude-status.service`:
- `Restart=on-failure`
- `After=graphical-session.target` / `WantedBy=graphical-session.target`
- `ExecStart` path written by `install.sh` at install time (absolute path)

`install.sh`:
1. `pip install --user -r requirements.txt`
2. Generates `~/.config/systemd/user/claude-status.service` with `ExecStart` set to the absolute path of `tray.py` (resolved via `$(realpath "$SCRIPT_DIR/tray.py")` where `SCRIPT_DIR` is the directory containing `install.sh`)
3. `systemctl --user enable --now claude-status`
4. If the service is already running, restarts it

## GNOME/Wayland Note

On GNOME/Wayland, the **AppIndicator and KStatusNotifierItem Support** GNOME Shell extension is required for tray icons to appear. The install script detects GNOME via `gnome-shell --version` and checks for the extension via `gnome-extensions list`, printing a reminder if it is missing.
