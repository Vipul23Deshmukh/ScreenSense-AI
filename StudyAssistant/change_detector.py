"""
change_detector.py — Frame-diff based screen change detector

Strategy:
  1. Resize both frames to a small thumbnail (fast, configured by CHANGE_RESIZE_FACTOR)
  2. Convert to grayscale
  3. Apply Gaussian blur to remove minor noise/artifacts
  4. Compute absolute difference via OpenCV
  5. Threshold the difference (CHANGE_DIFF_THRESHOLD) → binary mask
  6. Count "changed" pixels in the mask
  7. If changed-pixel-fraction > CHANGE_THRESHOLD or total pixels > CHANGE_MIN_AREA
     → signal a change
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

import config
from utils import setup_logger

logger = setup_logger("change_detector")


# ─────────────────────────────────────────────────────────
#  DATA MODEL
# ─────────────────────────────────────────────────────────

@dataclass
class DiffResult:
    """Detailed result of a frame comparison."""
    changed: bool            # Did the frame change enough to trigger?
    fraction: float          # Fraction of pixels that changed (0.0 to 1.0)
    changed_pixels: int      # Absolute number of changed pixels
    diff_mask: np.ndarray    # Binary mask of changed pixels (for debugging)


# ─────────────────────────────────────────────────────────
#  DETECTOR CLASS
# ─────────────────────────────────────────────────────────

class ChangeDetector:
    """
    Compares successive screen frames to detect meaningful visual changes.
    """

    def __init__(
        self,
        threshold: float = getattr(config, "CHANGE_THRESHOLD", 0.04),
        resize_factor: float = getattr(config, "CHANGE_RESIZE_FACTOR", 0.25),
        diff_threshold: int = getattr(config, "CHANGE_DIFF_THRESHOLD", 25),
        min_area: int = getattr(config, "CHANGE_MIN_AREA", 200),
    ) -> None:
        self.threshold = threshold
        self.resize_factor = resize_factor
        self.diff_threshold = diff_threshold
        self.min_area = min_area

        self._prev_frame: Optional[np.ndarray] = None
        self._frame_count: int = 0
        
        logger.info(
            "ChangeDetector initialised (threshold=%.2f, diff_thresh=%d, min_area=%d)",
            self.threshold, self.diff_threshold, self.min_area
        )

    # ──────────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────────

    def has_changed(self, frame: np.ndarray) -> bool:
        """
        Convenience method: returns True if the new frame differs meaningfully 
        from the last one.
        
        Args:
            frame: BGR NumPy array from ScreenCapture.grab_numpy()
        """
        result = self.detect(frame)
        return result.changed

    def detect(self, frame: np.ndarray) -> DiffResult:
        """
        Perform full change detection on the given frame.
        
        Returns:
            DiffResult containing boolean status, metrics, and the diff mask.
        """
        small = self._preprocess(frame)
        self._frame_count += 1

        if self._prev_frame is None:
            self._prev_frame = small
            # Return an empty/false result on the very first frame
            mask = np.zeros_like(small)
            return DiffResult(False, 0.0, 0, mask)

        result = self._compute_diff(self._prev_frame, small)

        if result.changed:
            logger.debug(
                "Change detected (%.2f%% pixels, %d px, frame #%d)",
                result.fraction * 100, result.changed_pixels, self._frame_count
            )
            self._prev_frame = small   # update reference frame only on significant change
            
        return result

    def reset(self) -> None:
        """Clear the stored previous frame (force next frame to be baseline)."""
        self._prev_frame = None
        self._frame_count = 0
        logger.debug("ChangeDetector reset")

    # ──────────────────────────────────────────────
    #  Internal helpers
    # ──────────────────────────────────────────────

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Resize, grayscale, and blur for fast, robust comparison."""
        h, w = frame.shape[:2]
        new_w = max(1, int(w * self.resize_factor))
        new_h = max(1, int(h * self.resize_factor))
        
        # 1. Resize
        small = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # 2. Grayscale
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # 3. Gaussian Blur (removes minor noise/compression artifacts)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        return blurred

    def _compute_diff(self, prev: np.ndarray, curr: np.ndarray) -> DiffResult:
        """
        Compute pixel-level absolute difference.
        """
        # Absolute difference
        diff = cv2.absdiff(prev, curr)
        
        # Threshold to create a binary mask of "changed" pixels
        _, thresh = cv2.threshold(
            diff, self.diff_threshold, 255, cv2.THRESH_BINARY
        )
        
        n_changed = int(np.count_nonzero(thresh))
        total = thresh.size
        fraction = n_changed / total if total > 0 else 0.0
        
        changed = (fraction >= self.threshold) or (n_changed >= self.min_area)
        
        return DiffResult(
            changed=changed,
            fraction=fraction,
            changed_pixels=n_changed,
            diff_mask=thresh
        )