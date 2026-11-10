#!/usr/bin/env python3
"""Measure internet speed repeatedly and show a graphical terminal summary.

Install in your virtual environment:
    python -m pip install speedtest-cli

Run:
    python internet_speed_test_v1.0.0.py

Edit NUM_TESTS and the thresholds below to suit your connection.
"""

import os
import sys
import time
from statistics import fmean

try:
    import speedtest
except ImportError:
    sys.exit(
        "Missing dependency. Activate your virtual environment, then run:\n"
        "  python -m pip install speedtest-cli"
    )


# Number of download/upload samples used for min, max, and average.
NUM_TESTS = 3

# Classification thresholds in Mbps. Both average speeds must meet a level.
EXCELLENT_DOWNLOAD_MBPS = 100.0
EXCELLENT_UPLOAD_MBPS = 20.0
GOOD_DOWNLOAD_MBPS = 20.0
GOOD_UPLOAD_MBPS = 5.0
NEUTRAL_DOWNLOAD_MBPS = 10.0
NEUTRAL_UPLOAD_MBPS = 2.0
BAD_DOWNLOAD_MBPS = 5.0
BAD_UPLOAD_MBPS = 1.0

# The bar graphics fill at these speeds. Change them if you have a faster plan.
DOWNLOAD_BAR_SCALE_MBPS = 300.0
UPLOAD_BAR_SCALE_MBPS = 100.0

BOX_WIDTH = 68
RESET = "\033[0m"
COLORS = {
    "cyan": "\033[96m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "orange": "\033[38;5;208m",
    "red": "\033[91m",
    "magenta": "\033[95m",
    "dim": "\033[2m",
    "bold": "\033[1m",
}


def colorize(text: str, color: str) -> str:
    """Add terminal color when stdout is an interactive, color-capable terminal."""
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return text
    return f"{COLORS.get(color, '')}{text}{RESET}"


def individual_rating(value: float, excellent: float, good: float, neutral: float, bad: float) -> tuple[str, str]:
    """Rate one direction using that direction's thresholds."""
    if value >= excellent:
        return "EXCELLENT", "green"
    if value >= good:
        return "GOOD", "cyan"
    if value >= neutral:
        return "NEUTRAL", "yellow"
    if value >= bad:
        return "BAD", "orange"
    return "WORST", "red"


def quality_rating(avg_download: float, avg_upload: float) -> tuple[str, str]:
    """Rate the connection using both average download and upload speed."""
    if avg_download >= EXCELLENT_DOWNLOAD_MBPS and avg_upload >= EXCELLENT_UPLOAD_MBPS:
        return "EXCELLENT", "green"
    if avg_download >= GOOD_DOWNLOAD_MBPS and avg_upload >= GOOD_UPLOAD_MBPS:
        return "GOOD", "cyan"
    if avg_download >= NEUTRAL_DOWNLOAD_MBPS and avg_upload >= NEUTRAL_UPLOAD_MBPS:
        return "NEUTRAL", "yellow"
    if avg_download >= BAD_DOWNLOAD_MBPS and avg_upload >= BAD_UPLOAD_MBPS:
        return "BAD", "orange"
    return "WORST", "red"


def bar(value: float, scale: float, width: int = 24) -> str:
    """Draw a terminal bar. It fills completely at `scale` Mbps."""
    if scale <= 0:
        return "░" * width
    filled = round(max(0.0, min(value / scale, 1.0)) * width)
    return "█" * filled + "░" * (width - filled)


def print_box(title: str, rows: list[tuple[str, str]]) -> None:
    """Print a Unicode box with aligned, optionally colored rows."""
    border = "╔" + "═" * BOX_WIDTH + "╗"
    bottom = "╚" + "═" * BOX_WIDTH + "╝"
    print(colorize(border, "cyan"))
    heading = title.center(BOX_WIDTH)
    print(colorize("║" + heading + "║", "bold"))
    print(colorize("╠" + "═" * BOX_WIDTH + "╣", "cyan"))
    for text, shade in rows:
        # Keep rows within the box even if a server name is unusually long.
        content = text[:BOX_WIDTH].ljust(BOX_WIDTH)
        print("║" + colorize(content, shade) + "║")
    print(colorize(bottom, "cyan"))


def stats_rows(label: str, samples: list[float], scale: float, shade: str) -> list[tuple[str, str]]:
    minimum = min(samples)
    maximum = max(samples)
    average = fmean(samples)
    symbol = "↓" if label == "DOWNLOAD" else "↑"
    return [
        (f"{symbol} {label}", shade),
        (f"  Min  {minimum:8.2f} Mbps   ({minimum / 8:6.2f} MB/s)", "dim"),
        (f"  Max  {maximum:8.2f} Mbps   ({maximum / 8:6.2f} MB/s)", "dim"),
        (f"  Avg  {average:8.2f} Mbps   ({average / 8:6.2f} MB/s)", "bold"),
        (f"  [{bar(average, scale)}]  (bar scale: {scale:g} Mbps)", shade),
        ("", "dim"),
    ]


def main() -> int:
    if NUM_TESTS < 1:
        print("NUM_TESTS must be at least 1.", file=sys.stderr)
        return 1

    download_samples: list[float] = []
    upload_samples: list[float] = []
    started = time.perf_counter()

    try:
        print_box("*** INTERNET SPEED TEST ***", [("Finding the best nearby test server…", "cyan")])
        tester = speedtest.Speedtest(secure=True, timeout=20)
        server = tester.get_best_server()
        server_name = (
            f"{server.get('sponsor', 'Unknown')} — "
            f"{server.get('name', 'Unknown')}, {server.get('country', 'Unknown')}"
        )
        idle_ping = tester.results.ping
        print_box(
            "◉  TEST SERVER",
            [
                (server_name[:BOX_WIDTH], "cyan"),
                (f"Idle ping: {idle_ping:.1f} ms", "magenta"),
                (f"Samples: {NUM_TESTS}  |  Measuring download and upload", "dim"),
            ],
        )

        for index in range(NUM_TESTS):
            print(colorize(f"\n  ◆ TEST {index + 1:02d}/{NUM_TESTS:02d}", "bold"))
            download_mbps = tester.download() / 1_000_000
            upload_mbps = tester.upload() / 1_000_000
            download_samples.append(download_mbps)
            upload_samples.append(upload_mbps)
            print(colorize(f"    ↓ Download  {bar(download_mbps, DOWNLOAD_BAR_SCALE_MBPS, 18)}  {download_mbps:.2f} Mbps", "green"))
            print(colorize(f"    ↑ Upload    {bar(upload_mbps, UPLOAD_BAR_SCALE_MBPS, 18)}  {upload_mbps:.2f} Mbps", "magenta"))

    except speedtest.SpeedtestException as exc:
        print(colorize(f"\n✖ Speed test failed: {exc}", "red"), file=sys.stderr)
        print("Check your connection, then try again.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(colorize(f"\n✖ Unexpected error: {exc}", "red"), file=sys.stderr)
        return 1

    avg_download = fmean(download_samples)
    avg_upload = fmean(upload_samples)
    download_rating, download_rating_color = individual_rating(
        avg_download,
        EXCELLENT_DOWNLOAD_MBPS,
        GOOD_DOWNLOAD_MBPS,
        NEUTRAL_DOWNLOAD_MBPS,
        BAD_DOWNLOAD_MBPS,
    )
    upload_rating, upload_rating_color = individual_rating(
        avg_upload,
        EXCELLENT_UPLOAD_MBPS,
        GOOD_UPLOAD_MBPS,
        NEUTRAL_UPLOAD_MBPS,
        BAD_UPLOAD_MBPS,
    )
    rating, rating_color = quality_rating(avg_download, avg_upload)

    rows: list[tuple[str, str]] = []
    rows.extend(stats_rows("DOWNLOAD", download_samples, DOWNLOAD_BAR_SCALE_MBPS, "green"))
    rows.extend(stats_rows("UPLOAD", upload_samples, UPLOAD_BAR_SCALE_MBPS, "magenta"))
    rows.extend(
        [
            (f"◉  Idle ping: {idle_ping:.1f} ms", "cyan"),
            (f"↓  DOWNLOAD RATING:  {download_rating}", download_rating_color),
            (f"↑  UPLOAD RATING:    {upload_rating}", upload_rating_color),
            (f"★  OVERALL RATING:   {rating}", rating_color),
            (f"   Based on averages: ↓ {avg_download:.2f} Mbps  |  ↑ {avg_upload:.2f} Mbps", "dim"),
            (f"   Elapsed: {time.perf_counter() - started:.1f} seconds", "dim"),
        ]
    )
    print()
    print_box("*** YOUR INTERNET RESULTS ***", rows)

    print("\nOverall rating guide (both average speeds must meet the threshold):")
    print("Per-direction ratings use only that direction's average speed.")
    print(f"  {colorize('★ EXCELLENT', 'green')}  Download ≥ {EXCELLENT_DOWNLOAD_MBPS:g} Mbps and upload ≥ {EXCELLENT_UPLOAD_MBPS:g} Mbps")
    print(f"  {colorize('◆ GOOD', 'cyan')}       Download ≥ {GOOD_DOWNLOAD_MBPS:g} Mbps and upload ≥ {GOOD_UPLOAD_MBPS:g} Mbps")
    print(f"  {colorize('● NEUTRAL', 'yellow')}    Download ≥ {NEUTRAL_DOWNLOAD_MBPS:g} Mbps and upload ≥ {NEUTRAL_UPLOAD_MBPS:g} Mbps")
    print(f"  {colorize('● BAD', 'orange')}        Download ≥ {BAD_DOWNLOAD_MBPS:g} Mbps and upload ≥ {BAD_UPLOAD_MBPS:g} Mbps")
    print(f"  {colorize('✖ WORST', 'red')}      Below either Bad threshold")
    print("\nThresholds are general guidelines; Wi-Fi, ping, and your internet plan also matter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
