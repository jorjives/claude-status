# claude-status

A Linux system tray icon that shows the current Claude API status.

Polls [status.claude.com](https://status.claude.com) every 60 seconds and displays a colour-coded icon:

- **Green** — all systems operational
- **Orange** — minor incident
- **Red** — major/critical incident or status unavailable

Right-click the icon to open the full status page or quit.

## Requirements

- Python 3
- Linux with a system tray (X11 or Wayland)
- AppIndicator support (installed automatically)
- GNOME users need the [AppIndicator extension](https://extensions.gnome.org/extension/615/appindicator-support/)

## Install

```bash
git clone https://github.com/jorjives/claude-status.git
cd claude-status
./install.sh
```

The install script:
1. Installs Python dependencies (`pystray`, `Pillow`)
2. Installs the AppIndicator system library
3. Sets up a systemd user service that starts automatically on login

## Install from .deb

Download the latest `.deb` from [GitHub Releases](https://github.com/jorjives/claude-status/releases/latest):

```bash
sudo apt install ./claude-status_*_all.deb
```

The service starts automatically on your next login. To start it immediately:

```bash
systemctl --user start claude-status
```

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

## Development

After cloning, set up git hooks:

```bash
git config core.hooksPath .githooks
```

This runs tests automatically before each push.

## Running tests

```bash
PYSTRAY_BACKEND=xorg python3 -m pytest tests/ -v
```
