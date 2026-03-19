import sys
import os
os.environ.setdefault("PYSTRAY_BACKEND", "xorg")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tray import _hex_to_rgba, make_image, INDICATOR_COLORS, ERROR_COLOR, SPARKLE_B64


def test_hex_to_rgba_green():
    assert _hex_to_rgba("#4CAF50") == (76, 175, 80, 255)


def test_hex_to_rgba_red():
    assert _hex_to_rgba("#F44336") == (244, 67, 54, 255)


def test_make_image_size():
    img = make_image("#4CAF50")
    assert img.size == (64, 64)


def test_make_image_mode():
    img = make_image("#4CAF50")
    assert img.mode == "RGBA"


def test_indicator_none_is_green():
    assert INDICATOR_COLORS["none"] == "#4CAF50"


def test_indicator_minor_is_orange():
    assert INDICATOR_COLORS["minor"] == "#FF9800"


def test_indicator_major_is_red():
    assert INDICATOR_COLORS["major"] == "#F44336"


def test_indicator_critical_is_red():
    assert INDICATOR_COLORS["critical"] == "#F44336"


def test_error_color_is_red():
    assert ERROR_COLOR == "#F44336"


def test_sparkle_b64_is_valid_png():
    import base64
    data = base64.b64decode(SPARKLE_B64)
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
