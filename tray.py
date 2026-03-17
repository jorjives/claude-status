#!/usr/bin/env python3
import json
import threading
import time
import urllib.request
import webbrowser

import pystray
from PIL import Image, ImageDraw

STATUS_URL = "https://status.claude.com/api/v2/status.json"
STATUS_PAGE = "https://status.claude.com"
POLL_INTERVAL = 60

INDICATOR_COLORS = {
    "none": "#4CAF50",
    "minor": "#FF9800",
    "major": "#F44336",
    "critical": "#F44336",
}
ERROR_COLOR = "#F44336"


def _hex_to_rgba(hex_color: str) -> tuple:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return (r, g, b, 255)


def make_image(color_hex: str) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bg = _hex_to_rgba(color_hex)
    white = (255, 255, 255, 255)

    draw.ellipse([1, 1, size - 2, size - 2], fill=bg)

    cx = size // 2
    # Outer white A shape
    draw.polygon([(cx, 10), (10, 54), (54, 54)], fill=white)
    # Inner hollow (background color triangle)
    draw.polygon([(cx, 18), (22, 42), (42, 42)], fill=bg)
    # Crossbar (white rectangle over bottom of hollow)
    draw.rectangle([18, 38, 46, 44], fill=white)

    return img


def fetch_status() -> tuple[str, str]:
    with urllib.request.urlopen(STATUS_URL, timeout=10) as resp:
        data = json.loads(resp.read())
    indicator = data["status"]["indicator"]
    description = data["status"]["description"]
    return INDICATOR_COLORS.get(indicator, ERROR_COLOR), description


def _poll(icon: pystray.Icon) -> None:
    while True:
        try:
            color, description = fetch_status()
        except Exception:
            color, description = ERROR_COLOR, "Status unavailable"
        icon.icon = make_image(color)
        icon.title = description
        time.sleep(POLL_INTERVAL)


def main() -> None:
    menu = pystray.Menu(
        pystray.MenuItem("Open status page", lambda icon, item: webbrowser.open(STATUS_PAGE)),
        pystray.MenuItem("Quit", lambda icon, item: icon.stop()),
    )
    icon = pystray.Icon("claude-status", make_image(ERROR_COLOR), "Loading...", menu)
    threading.Thread(target=_poll, args=(icon,), daemon=True).start()
    icon.run()


if __name__ == "__main__":
    main()
