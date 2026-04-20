"""
capture.py — High-performance screen capture module for AI Study Assistant

Backends (tried in order):
  1. mss        — fastest, persistent context, zero-copy NumPy path
  2. pyautogui  — universal fallback

Public API
──────────
    cap = ScreenCapture(region=(left, top, width, height))  # or None = full screen

    # Single-shot captures
    frame: np.ndarray  = cap.grab_numpy()   # BGR uint8  ← fastest
    img:   PIL.Image   = cap.grab()         # RGB PIL

    # Continuous capture (generator — most efficient for live loops)
    for frame in cap.stream(fps_cap=30):
        process(frame)                       # frame is BGR ndarray
        if done: break

    # Runtime region update
    cap.set_region((x, y, w, h))

    # FPS diagnostics
    print(cap.fps)                           # measured FPS of last stream

    # Resource cleanup
    cap.close()                             # or use as context manager:
    with ScreenCapture() as cap:
        ...

Performance notes
─────────────────
• mss keeps one persistent mss() context — no per-frame object creation.
• grab_numpy() uses a zero-copy path: mss BGRA bytes → NumPy view → slice
  to BGR. No intermediate PIL object is created.
• stream() pre-allocates the output buffer once and reuses it every frame.
• pyautogui fallback is ~3-5× slower but works everywhere.
"""

from __future__ import annotations

import time
import threading
from typing import Generator, Iterator, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

import config
from utils import setup_logger

logger = setup_logger("capture")

# Type alias: (left, top, width, height) — all in pixels
Region = Optional[Tuple[int, int, int, int]]


# ─────────────────────────────────────────────────────────
#  PERFORMANCE TIMER  (lightweight FPS counter)
# ─────────────────────────────────────────────────────────

class _FPSCounter:
    """Rolling-window FPS counter (thread-safe)."""

    def __init__(self, window: int = 30) -> None:
        self._times: list[float] = []
        self._window = window
        self._lock   = threading.Lock()

    def tick(self) -> None:
        now = time.perf_counter()
        with self._lock:
            self._times.append(now)
            if len(self._times) > self._window:
                self._times.pop(0)

    @property
    def fps(self) -> float:
        with self._lock:
            if len(self._times) < 2:
                return 0.0
            span = self._times[-1] - self._times[0]
            return (len(self._times) - 1) / span if span > 0 else 0.0


# ─────────────────────────────────────────────────────────
#  SCREEN CAPTURE
# ─────────────────────────────────────────────────────────

class ScreenCapture:
    """
    High-performance screen grabber.

    Parameters
    ----------
    region : (left, top, width, height) or None
        Capture region in screen pixels.
        Pass None (default) to capture the full primary monitor.
    """

    def __init__(self, region: Region = None) -> None:
        self.region     = region if region is not None else config.CAPTURE_REGION
        self._sct       = None          # mss context (None if unavailable)
        self._monitor   = {}            # cached mss monitor dict
        self._buf: Optional[np.ndarray] = None  # pre-allocated stream buffer
        self._fps_ctr   = _FPSCounter()

        self._init_mss()

    # ──────────────────────────────────────────────
    #  Initialisation helpers
    # ──────────────────────────────────────────────

    def _init_mss(self) -> None:
        """Try to open a persistent mss context."""
        try:
            import mss as _mss
            self._sct = _mss.mss()
            self._monitor = self._build_monitor()
            logger.info(
                "mss backend ready  region=%s  monitor=%s",
                self.region, self._monitor,
            )
        except ImportError:
            logger.warning("mss not installed — falling back to pyautogui")
            self._sct = None

    def _build_monitor(self) -> dict:
        """Construct the mss monitor dict from self.region."""
        if self.region:
            l, t, w, h = self.region
            return {"left": l, "top": t, "width": w, "height": h}
        # Full primary monitor (index 1 = first real monitor, 0 = virtual all-monitors)
        return self._sct.monitors[1]

    # ──────────────────────────────────────────────
    #  Single-shot public API
    # ──────────────────────────────────────────────

    def grab_numpy(self) -> np.ndarray:
        """
        Capture one frame and return it as a BGR NumPy array (H × W × 3, uint8).

        This is the **fastest** single-shot path:
          mss BGRA bytes  →  NumPy view (no copy)  →  BGR slice (no copy)
        """
        if self._sct:
            return self._grab_mss_numpy()
        return self._grab_pyautogui_numpy()

    def grab(self) -> Image.Image:
        """
        Capture one frame and return it as a PIL RGB image.
        Slightly slower than grab_numpy() due to the extra conversion.
        """
        bgr = self.grab_numpy()
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    # ──────────────────────────────────────────────
    #  Continuous streaming generator
    # ──────────────────────────────────────────────

    def stream(
        self,
        fps_cap: float = 0,
        max_frames: int = 0,
    ) -> Generator[np.ndarray, None, None]:
        """
        Yield BGR NumPy frames continuously.

        Parameters
        ----------
        fps_cap : float
            Maximum frames per second (0 = unlimited).
        max_frames : int
            Stop after this many frames (0 = run forever).

        Yields
        ------
        np.ndarray
            BGR uint8 frame, shape (H, W, 3).

        Example
        -------
            with ScreenCapture(region=(0, 0, 1280, 720)) as cap:
                for frame in cap.stream(fps_cap=30):
                    cv2.imshow("stream", frame)
                    if cv2.waitKey(1) == 27:
                        break
        """
        min_interval = (1.0 / fps_cap) if fps_cap > 0 else 0.0
        count        = 0
        t_last       = time.perf_counter()

        while True:
            # ── FPS cap ──────────────────────────────────
            if min_interval:
                elapsed = time.perf_counter() - t_last
                sleep   = min_interval - elapsed
                if sleep > 0:
                    time.sleep(sleep)
            t_last = time.perf_counter()

            # ── Grab frame ───────────────────────────────
            frame = self._grab_into_buffer()
            self._fps_ctr.tick()

            yield frame

            count += 1
            if max_frames and count >= max_frames:
                break

    # ──────────────────────────────────────────────
    #  Diagnostics
    # ──────────────────────────────────────────────

    @property
    def fps(self) -> float:
        """Rolling measured FPS of the active / most recent stream."""
        return self._fps_ctr.fps

    @property
    def frame_size(self) -> Tuple[int, int]:
        """Return (width, height) of the capture region."""
        if self.region:
            _, _, w, h = self.region
            return w, h
        if self._sct:
            m = self._monitor
            return m["width"], m["height"]
        return 0, 0

    # ──────────────────────────────────────────────
    #  Runtime reconfiguration
    # ──────────────────────────────────────────────

    def set_region(self, region: Region) -> None:
        """
        Change the capture region at runtime.
        Also resets the pre-allocated buffer so it is resized on the next grab.
        """
        self.region = region
        self._buf   = None      # force buffer re-allocation
        if self._sct:
            self._monitor = self._build_monitor()
        logger.info("Capture region updated → %s", region)

    # ──────────────────────────────────────────────
    #  Context manager
    # ──────────────────────────────────────────────

    def __enter__(self) -> "ScreenCapture":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def close(self) -> None:
        """Release the mss context and free the buffer."""
        if self._sct:
            try:
                self._sct.close()
            except Exception:
                pass
            self._sct = None
        self._buf = None
        logger.debug("ScreenCapture closed")

    # ──────────────────────────────────────────────
    #  Internal fast paths
    # ──────────────────────────────────────────────

    def _grab_mss_numpy(self) -> np.ndarray:
        """
        Zero-copy mss → BGR NumPy path.

        mss.grab() returns a ScreenShot with raw BGRA bytes.
        We view that memory as a (H, W, 4) uint8 array and slice off
        the alpha channel → (H, W, 3) BGR.  No extra allocation.
        """
        raw = self._sct.grab(self._monitor)
        # View raw bytes as BGRA without copying
        bgra = np.frombuffer(raw.raw, dtype=np.uint8).reshape(
            (raw.height, raw.width, 4)
        )
        # Slice channels 0-2 → BGR (view, not copy)
        return bgra[:, :, :3]

    def _grab_pyautogui_numpy(self) -> np.ndarray:
        """pyautogui screenshot → BGR NumPy (fallback, slower)."""
        import pyautogui
        if self.region:
            l, t, w, h = self.region
            pil = pyautogui.screenshot(region=(l, t, w, h))
        else:
            pil = pyautogui.screenshot()
        rgb = np.array(pil, dtype=np.uint8)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    def _grab_into_buffer(self) -> np.ndarray:
        """
        Grab a frame, re-using the pre-allocated output buffer where possible.

        The buffer is only allocated once per (width × height) — subsequent
        frames copy mss bytes directly into the same memory block.
        """
        if self._sct:
            raw = self._sct.grab(self._monitor)
            h, w = raw.height, raw.width

            # Allocate buffer on first call or after region change
            if self._buf is None or self._buf.shape[:2] != (h, w):
                self._buf = np.empty((h, w, 3), dtype=np.uint8)

            # Copy BGR channels directly into the buffer
            bgra = np.frombuffer(raw.raw, dtype=np.uint8).reshape((h, w, 4))
            np.copyto(self._buf, bgra[:, :, :3])
            return self._buf
        else:
            # pyautogui path — no buffer optimisation (PIL allocation unavoidable)
            return self._grab_pyautogui_numpy()


# ─────────────────────────────────────────────────────────
#  MODULE-LEVEL CONVENIENCE
# ─────────────────────────────────────────────────────────

def grab_frame(region: Region = None) -> np.ndarray:
    """
    One-liner helper for a single frame grab.
    Creates a temporary ScreenCapture, grabs one frame, then cleans up.

    Use ScreenCapture directly in loops — this function is for scripts/tests.
    """
    with ScreenCapture(region=region) as cap:
        return cap.grab_numpy().copy()   # copy because context closes immediately