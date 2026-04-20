"""
test_change_detector.py — Interactive viewer to tune ChangeDetector thresholds.

Displays the live capture alongside the change detection binary mask.
When a change is detected, the border flashes red and the console logs the metrics.

Usage:
  python test_change_detector.py              # Full screen
  python test_change_detector.py --region     # Use configured region

Hotkeys:
  ESC / Q      — Quit
  R            — Toggle Region / Full-screen
  C            — Force detector reset (clear baseline frame)
"""

import argparse
import time

import cv2
import numpy as np

import config
from capture import ScreenCapture
from change_detector import ChangeDetector

WINDOW_NAME = "Change Detector Test"
REGION = (0, 0, 1280, 720)


def draw_hud(
    frame: np.ndarray,
    diff_mask: np.ndarray | None,
    changed: bool,
    fraction: float,
    pixels: int,
    use_region: tuple | None
) -> np.ndarray:
    """Draw debug information and the diff mask on the frame."""
    out = frame.copy()
    h, w = out.shape[:2]

    # Flash a red border if change detected
    if changed:
        cv2.rectangle(out, (0, 0), (w-1, h-1), (0, 0, 255), 6)

    # Dark background for text
    cv2.rectangle(out, (0, 0), (w, 40), (20, 20, 20), -1)
    
    # Overlay the diff mask as a red tint in the bottom-right corner if available
    if diff_mask is not None:
        # Resize mask back to full size for display
        mask_large = cv2.resize(diff_mask, (w, h), interpolation=cv2.INTER_NEAREST)
        
        # Create a red overlay where pixels changed
        red_tint = np.zeros_like(out)
        red_tint[:, :, 2] = mask_large  # Red channel
        
        # Blend the red tint over the original frame
        out = cv2.addWeighted(out, 1.0, red_tint, 0.5, 0)

    # Info text
    region_str = f"Region {use_region}" if use_region else "Full Screen"
    status = "CHANGED!" if changed else "Idle"
    color = (0, 255, 0) if not changed else (0, 0, 255)
    
    text = (
        f"[{status}]  Changed: {fraction*100:.2f}% ({pixels} px)  |  "
        f"Thresh: {config.CHANGE_THRESHOLD*100:.1f}%  |  {region_str}  |  "
        f"[ESC] quit  [R] toggle region  [C] reset"
    )
    cv2.putText(out, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Test script for ChangeDetector")
    parser.add_argument("--region", action="store_true", help="Preview with REGION crop")
    args = parser.parse_args()

    use_region = REGION if args.region else None
    
    detector = ChangeDetector()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 960, 540)

    print(f"\n{'─'*55}")
    print(f"  Change Detector Test Started")
    print(f"  Region : {use_region or 'full screen'}")
    print(f"  Thresh : {detector.threshold*100:.2f}% (min area: {detector.min_area})")
    print(f"  Press ESC or Q to quit")
    print(f"{'─'*55}\n")

    with ScreenCapture(region=use_region) as cap:
        for frame in cap.stream(fps_cap=30):
            # ── 1. Run detection ──
            t0 = time.perf_counter()
            result = detector.detect(frame)
            latency_ms = (time.perf_counter() - t0) * 1000

            if result.changed:
                print(f"⚡ Change: {result.fraction*100:5.2f}% ({result.changed_pixels:5d} px) in {latency_ms:.1f}ms")

            # ── 2. Draw HUD and display ──
            hud = draw_hud(
                frame, 
                result.diff_mask, 
                result.changed, 
                result.fraction, 
                result.changed_pixels,
                use_region
            )
            cv2.imshow(WINDOW_NAME, hud)

            # ── 3. Handle hotkeys ──
            key = cv2.waitKey(1) & 0xFF
            
            if key in (27, ord("q"), ord("Q")):  # ESC / Q
                break
            elif key in (ord("r"), ord("R")):    # R → toggle region
                use_region = None if use_region else REGION
                cap.set_region(use_region)
                detector.reset()
                print(f"  Region toggled → {use_region or 'full screen'}")
            elif key in (ord("c"), ord("C")):    # C → reset baseline
                detector.reset()
                print("  Baseline frame reset")

    cv2.destroyAllWindows()
    print("\n  Done.")

if __name__ == "__main__":
    main()
