"""
test_capture.py — Interactive OpenCV viewer for capture.py

Modes (choose with CLI flag or menu):
  1. Full-screen live preview    (default)
  2. Region-based live preview
  3. Single-shot benchmark       (grab N frames, report FPS)
  4. Comparison: mss vs pyautogui speed

Usage:
  python test_capture.py              # full-screen live preview
  python test_capture.py --region     # region preview (edit REGION below)
  python test_capture.py --bench      # benchmark mode
  python test_capture.py --compare    # backend speed comparison

Hotkeys (live preview):
  ESC / Q      — quit
  S            — save current frame as PNG
  R            — toggle region / full-screen
  +  /  -      — increase / decrease FPS cap
  SPACE        — pause / resume
"""

import sys
import time
import argparse
import datetime

import cv2
import numpy as np

# ── Import our module ──────────────────────────────────────────────────
from capture import ScreenCapture, grab_frame

# ── Edit this region to focus on a specific area ──────────────────────
REGION = (0, 0, 1280, 720)   # (left, top, width, height)

# ── Display settings ──────────────────────────────────────────────────
DEFAULT_FPS_CAP  = 30        # target FPS for the preview window
WINDOW_NAME      = "AI Study Assistant — Screen Capture Test"
OVERLAY_COLOR    = (0, 255, 120)    # BGR green for HUD text
OVERLAY_FONT     = cv2.FONT_HERSHEY_SIMPLEX


# ─────────────────────────────────────────────────────────
#  HUD OVERLAY  (drawn on each preview frame)
# ─────────────────────────────────────────────────────────

def draw_hud(
    frame:   np.ndarray,
    fps:     float,
    cap_fps: int,
    paused:  bool,
    region:  tuple | None,
) -> np.ndarray:
    """Burn a semi-transparent info bar onto the frame (non-destructive copy)."""
    out  = frame.copy()
    h, w = out.shape[:2]

    # Dark bar at the top
    overlay = out.copy()
    cv2.rectangle(overlay, (0, 0), (w, 36), (10, 10, 10), -1)
    cv2.addWeighted(overlay, 0.65, out, 0.35, 0, out)

    region_str = f"Region {region}" if region else "Full Screen"
    status     = "⏸ PAUSED" if paused else f"FPS cap: {cap_fps}"
    text       = (
        f"  Measured: {fps:5.1f} fps   |   {region_str}   |   {status}"
        f"   |   [ESC] quit  [S] save  [R] toggle region  [SPACE] pause"
    )
    cv2.putText(out, text, (6, 24), OVERLAY_FONT, 0.45, OVERLAY_COLOR, 1, cv2.LINE_AA)
    return out


# ─────────────────────────────────────────────────────────
#  MODE 1 & 2 — LIVE PREVIEW
# ─────────────────────────────────────────────────────────

def run_live_preview(start_region: tuple | None = None) -> None:
    """
    Open a resizable OpenCV window showing the live screen capture.
    Handles all keyboard controls in-loop.
    """
    fps_cap    = DEFAULT_FPS_CAP
    use_region = start_region       # None = full screen
    paused     = False
    frame_num  = 0

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 960, 540)

    with ScreenCapture(region=use_region) as cap:
        print(f"\n{'─'*55}")
        print(f"  Live preview started")
        print(f"  Region  : {use_region or 'full screen'}")
        print(f"  FPS cap : {fps_cap}")
        print(f"  Press ESC or Q to quit")
        print(f"{'─'*55}\n")

        for frame in cap.stream(fps_cap=fps_cap):
            if not paused:
                frame_num += 1
                hud = draw_hud(frame, cap.fps, fps_cap, paused, use_region)
                cv2.imshow(WINDOW_NAME, hud)
            else:
                # Show last frame with PAUSED indicator
                cv2.imshow(WINDOW_NAME, hud)  # type: ignore[possibly-undefined]

            key = cv2.waitKey(1) & 0xFF

            # ── Hotkey handling ──────────────────────
            if key in (27, ord("q"), ord("Q")):          # ESC / Q → quit
                break

            elif key == ord(" "):                          # SPACE → pause
                paused = not paused
                print(f"  {'Paused' if paused else 'Resumed'}")

            elif key in (ord("s"), ord("S")):              # S → save frame
                ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fn  = f"capture_{ts}.png"
                cv2.imwrite(fn, frame)
                print(f"  Saved → {fn}")

            elif key in (ord("r"), ord("R")):              # R → toggle region
                use_region = None if use_region else start_region or REGION
                cap.set_region(use_region)
                print(f"  Region toggled → {use_region or 'full screen'}")

            elif key == ord("+"):                           # + → raise FPS cap
                fps_cap = min(fps_cap + 5, 120)
                print(f"  FPS cap → {fps_cap}")

            elif key == ord("-"):                           # - → lower FPS cap
                fps_cap = max(fps_cap - 5, 1)
                print(f"  FPS cap → {fps_cap}")

    cv2.destroyAllWindows()
    print(f"\n  Done. Captured {frame_num} frames.")


# ─────────────────────────────────────────────────────────
#  MODE 3 — BENCHMARK
# ─────────────────────────────────────────────────────────

def run_benchmark(
    n_frames: int  = 200,
    region:   tuple | None = None,
) -> None:
    """
    Grab N frames as fast as possible; report throughput and latency stats.
    """
    print(f"\n{'─'*55}")
    print(f"  Benchmark: {n_frames} frames, region={region or 'full screen'}")
    print(f"{'─'*55}")

    latencies: list[float] = []

    with ScreenCapture(region=region) as cap:
        # Warm-up
        for _ in range(5):
            cap.grab_numpy()

        # Timed run
        t_start = time.perf_counter()
        for _ in range(n_frames):
            t0 = time.perf_counter()
            cap.grab_numpy()
            latencies.append((time.perf_counter() - t0) * 1000)  # ms
        t_total = time.perf_counter() - t_start

    avg   = sum(latencies) / len(latencies)
    mn    = min(latencies)
    mx    = max(latencies)
    p95   = sorted(latencies)[int(0.95 * len(latencies))]
    fps   = n_frames / t_total

    print(f"\n  Frames    : {n_frames}")
    print(f"  Total     : {t_total:.3f} s")
    print(f"  Throughput: {fps:.1f} fps")
    print(f"  Latency   : avg={avg:.2f} ms   min={mn:.2f}   max={mx:.2f}   p95={p95:.2f}")
    print()


# ─────────────────────────────────────────────────────────
#  MODE 4 — BACKEND COMPARISON
# ─────────────────────────────────────────────────────────

def run_comparison(n_frames: int = 100) -> None:
    """
    Time mss vs. pyautogui side-by-side.
    """
    print(f"\n{'─'*55}")
    print(f"  Backend comparison: {n_frames} frames each")
    print(f"{'─'*55}")

    results: dict[str, float] = {}

    # ── mss ──────────────────────────────────────────────
    try:
        import mss as _mss
        with _mss.mss() as sct:
            monitor = sct.monitors[1]
            # warm-up
            for _ in range(3):
                sct.grab(monitor)
            t0 = time.perf_counter()
            for _ in range(n_frames):
                raw  = sct.grab(monitor)
                bgra = np.frombuffer(raw.raw, dtype=np.uint8).reshape(
                    (raw.height, raw.width, 4)
                )
                _ = bgra[:, :, :3]
            results["mss (zero-copy)"] = n_frames / (time.perf_counter() - t0)
    except ImportError:
        print("  mss not installed — skipping")

    # ── mss + PIL (old path) ─────────────────────────────
    try:
        import mss as _mss
        from PIL import Image as _Image
        with _mss.mss() as sct:
            monitor = sct.monitors[1]
            for _ in range(3):
                sct.grab(monitor)
            t0 = time.perf_counter()
            for _ in range(n_frames):
                raw = sct.grab(monitor)
                _   = _Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            results["mss (via PIL)"] = n_frames / (time.perf_counter() - t0)
    except ImportError:
        pass

    # ── pyautogui ────────────────────────────────────────
    try:
        import pyautogui
        import cv2 as _cv2
        # warm-up
        for _ in range(2):
            pyautogui.screenshot()
        t0 = time.perf_counter()
        for _ in range(n_frames):
            pil = pyautogui.screenshot()
            _   = _cv2.cvtColor(np.array(pil, dtype=np.uint8), _cv2.COLOR_RGB2BGR)
        results["pyautogui"] = n_frames / (time.perf_counter() - t0)
    except ImportError:
        print("  pyautogui not installed — skipping")

    # ── Results table ─────────────────────────────────────
    print()
    if results:
        best = max(results.values())
        for name, fps in sorted(results.items(), key=lambda x: -x[1]):
            bar    = "█" * int(fps / best * 30)
            marker = " ← fastest" if fps == best else ""
            print(f"  {name:<22} {fps:>6.1f} fps  {bar}{marker}")
    print()


# ─────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Test script for capture.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument("--region",  action="store_true", help="Preview with REGION crop")
    g.add_argument("--bench",   action="store_true", help="Benchmark mode")
    g.add_argument("--compare", action="store_true", help="mss vs pyautogui comparison")
    p.add_argument("--frames",  type=int, default=200, help="Frames for --bench/--compare")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    if args.bench:
        run_benchmark(n_frames=args.frames, region=REGION)
    elif args.compare:
        run_comparison(n_frames=args.frames)
    elif args.region:
        run_live_preview(start_region=REGION)
    else:
        # Default: full-screen live preview
        run_live_preview(start_region=None)


if __name__ == "__main__":
    main()