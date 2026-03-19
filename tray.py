#!/usr/bin/env python3
import base64
import json
import os
from io import BytesIO
import tempfile
import threading
import time
import urllib.request
import webbrowser

import pystray
from PIL import Image, ImageDraw


class _Icon(pystray.Icon):
    """pystray saves temp icons without a .png extension; AppIndicator
    won't load them. Override to add the suffix."""
    def _update_fs_icon(self):
        old = getattr(self, '_icon_path', None)
        self._icon_path = tempfile.mktemp(suffix='.png')
        with open(self._icon_path, 'wb') as f:
            self.icon.save(f, 'PNG')
        self._icon_valid = True
        if old:
            try:
                os.remove(old)
            except OSError:
                pass

STATUS_URL = "https://status.claude.com/api/v2/status.json"
STATUS_PAGE = "https://status.claude.com"
POLL_INTERVAL = 60

ERROR_COLOR = "#F44336"
INDICATOR_COLORS = {
    "none": "#4CAF50",
    "minor": "#FF9800",
    "major": ERROR_COLOR,
    "critical": ERROR_COLOR,
}


def _hex_to_rgba(hex_color: str) -> tuple:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return (r, g, b, 255)


# Pre-rendered 40x40 white Claude sparkle on transparent background
SPARKLE_B64 = "iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAEtUlEQVR4nMWYfWhWVRzHv3c9my+1lDlbbxiVZFaI68WIGtI/wnpd1DSCgt4MKoLeGfYGFg16AcWmGUolscxFUYlFRUUqJTVtFWRLy+FsrbnZ2mwzt09/3PO4385z7/Pc59mqHxy49/f9nt/93t8959zfOVICA4qADUAv0AzMS9CnGFgApJI8Y0wGPMxo25GDfxSwzXHf/C8EfkCmXZqFf5XHPbHQZxcl5G2N8N2bhX+Jue6X9GtiRYUYcBpw0MvKEDArhr/O8JqzxK0B6oHa8RC5JOIzr4rh2iHRGMN5EBh2nAHg7LEKLAF+9AQeBKZHcLcbzpII/A4jLm1rkogoJZyxi4EpEfiVEVmsj+DtNXi1h9UAhyPi3JpE4EbToRWYG8F53wvcB1QYPAAGDX68wSqB/ghx+4BpSQRu9zr+Bdzmcc4EDnm85w1eYfztxl8G7IoQdwioyinOBamPCACwGphoeMsiXuQkh51n/BudLwV8FBP7rkTiXKBi4Gmix8hXwEzHKwd6PLzBYTXG95TzPRsj7rXE4jyhVUBbRMA/gBsc5yEPGwROAe40vlrgajJnLMD3wNEFCXQCyoA3Yt58DTAN+MXzLwceNffVQHdE/37Guu4ZobXAbzEZWOn52hg9PgdiXjD3kpKnyHKgMeZhvnXmwN/K8awUMBuYI0lBnkKvkbRSUkUubowNSDorCIKfXbypki6QVClpjqRzJM2WVOL4r+Ql0AWdLqlB0nUFCPxQ0juS5rl2hrInaX0AXCTpfEldkrol9bjWLaknCILhGKHXS1ohKfcfID8bkrRD0meSVgVAp6SMH76xA671KhS9V9I+Se2SjpW0dIyCdkv62rRtQRD0psEAWCTpRUkZxcG/YOnsbJb0uaQtQRB0ZOtw5PsTVi+lrh2jUPBESZPcdZGkyZImuOspkmZKujahuF2SGiW1StovadBgfzpfVxAEBxLGy26ERYNf2YyHHQY6CAvkVCGzuFzSE5IWSyrOo+tLklokzZdUpWRLVUM+wiYQluk9/sILfJIgM0PA7SbeLOAW4GXgp5g+7dk0pQMFwEJgt9e5w/kfML7mHCKHgftinnOCi7ecsHJ6Djgul7hKYEvEg14lLBaqXWYAfgDudtd9rsXZM0Dew8sKSwGPkFk578HtMYAZQJfzDwBzGan7PgXqvL6PAzvN/TognzF8RNzpwBde8GHgBaDUcUo8zj3O/667X084ZlsNp5Nw5n9sfJuAyfkK9JeOnXh7BmCFwd/GfS6ToWXu/govVhNh1b7a+DYTFg2JBa51HQcI9yiTPPxGE3wPUOb8pYyMxzrDb/JELnL+OkYq7W8wu79cAlPAyUDGuQ3hOEsfgfwNXGyw+UbEzcZfAew32O+42ekynB7HrcCpiTMZIa6M0UtNnYffb7DLPOwmL4sbDDYD2Or8TYWKKyIc0Gnb5GeY0RX3uREx3vNELjRYMfAkhW4FGL0R+hI3mz2OPbfJOA90n9rubb4rSExE4KmMrIffEnFE4TjpAT9EzLEvcLnh9Y2XwDLCpaAlKjOOs8BkpjNHvKWEh0trx0VgEgMeMwJbxjN20iPgXNZmrrNWyP+LEf7WXncT6MLxjP0Ppvsebyb0vVQAAAAASUVORK5CYII="


def _load_sparkle() -> Image.Image:
    buf = BytesIO(base64.b64decode(SPARKLE_B64))
    img = Image.open(buf)
    img.load()
    return img.convert("RGBA")


_sparkle = _load_sparkle()


def make_image(color_hex: str) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([1, 1, size - 2, size - 2], fill=_hex_to_rgba(color_hex))
    offset = (size - _sparkle.width) // 2
    img.paste(_sparkle, (offset, offset), _sparkle)
    return img


def fetch_status() -> tuple[str, str]:
    with urllib.request.urlopen(STATUS_URL, timeout=10) as resp:
        data = json.loads(resp.read())
    indicator = data["status"]["indicator"]
    description = data["status"]["description"]
    return INDICATOR_COLORS.get(indicator, ERROR_COLOR), description


def _poll(icon: pystray.Icon) -> None:
    prev_color = prev_desc = None
    while True:
        try:
            color, description = fetch_status()
        except Exception:
            color, description = ERROR_COLOR, "Status unavailable"
        if color != prev_color or description != prev_desc:
            icon.icon = make_image(color)
            icon.title = description
            prev_color, prev_desc = color, description
        time.sleep(POLL_INTERVAL)


def main() -> None:
    menu = pystray.Menu(
        pystray.MenuItem("Open status page", lambda icon, item: webbrowser.open(STATUS_PAGE)),
        pystray.MenuItem("Quit", lambda icon, item: icon.stop()),
    )
    icon = _Icon("claude-status", make_image(ERROR_COLOR), "Loading...", menu)
    threading.Thread(target=_poll, args=(icon,), daemon=True).start()
    icon.run()


if __name__ == "__main__":
    main()
