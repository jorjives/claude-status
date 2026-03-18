#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAY_PY="$(realpath "$SCRIPT_DIR/tray.py")"
PYTHON="$(which python3)"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "Installing Python dependencies..."
pip3 install --user --break-system-packages -r "$SCRIPT_DIR/requirements.txt"

echo "Installing AppIndicator typelib (requires sudo)..."
sudo apt-get install -y gir1.2-ayatanaappindicator3-0.1

echo "Installing systemd user service..."
mkdir -p "$SERVICE_DIR"
cat > "$SERVICE_DIR/claude-status.service" <<EOF
[Unit]
Description=Claude Status System Tray Icon
After=graphical-session.target

[Service]
ExecStart=$PYTHON $TRAY_PY
Restart=on-failure

[Install]
WantedBy=graphical-session.target
EOF

systemctl --user daemon-reload
systemctl --user enable claude-status

if systemctl --user is-active --quiet claude-status; then
    systemctl --user restart claude-status
    echo "Service restarted."
else
    systemctl --user start claude-status
    echo "Service started."
fi

# GNOME check
if command -v gnome-shell &>/dev/null; then
    if ! gnome-extensions list 2>/dev/null | grep -qF "appindicatorsupport@rgcjonas.gmail.com"; then
        echo ""
        echo "NOTE: GNOME AppIndicator extension not found (appindicatorsupport@rgcjonas.gmail.com)."
        echo "The tray icon won't appear without it. Install it:"
        echo "  sudo apt install gnome-shell-extension-appindicator"
        echo "  or: https://extensions.gnome.org/extension/615/appindicator-support/"
        echo "Then log out and back in, and enable it with: gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com"
    fi
fi

# Developer setup: enable git hooks
if [ -d "$SCRIPT_DIR/.git" ]; then
    git -C "$SCRIPT_DIR" config core.hooksPath .githooks
    echo "Git hooks enabled."
fi

echo "Done."
