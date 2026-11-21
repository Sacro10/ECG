"""Offline ECG processing with no recording source or annotation dependency."""

from dataclasses import dataclass
from math import ceil

import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt


@dataclass
class Analysis:
    filtered: np.ndarray
    peaks: np.ndarray
    rr_seconds: np.ndarray
    interval_bpm: np.ndarray
    heart_rate_bpm: float


def analyze_ecg(signal, sampling_rate: float) -> Analysis:
    """Analyze an evenly sampled ECG. Peak indices refer to the input signal."""
    signal = np.asarray(signal, dtype=float)
    if signal.ndim != 1 or not np.all(np.isfinite(signal)):
        raise ValueError("ECG must be a finite one-dimensional signal.")
    if not np.isfinite(sampling_rate) or sampling_rate <= 40:
        raise ValueError("Sampling rate must exceed 40 Hz for the 20 Hz cutoff.")

    sos = butter(3, (5, 20), btype="bandpass", fs=sampling_rate, output="sos")
    pad_length = 3 * (2 * len(sos) + 1)
    if signal.size <= pad_length:
        raise ValueError(f"ECG must contain more than {pad_length} samples.")
    filtered = sosfiltfilt(sos, signal, padlen=pad_length)

    magnitude = np.abs(filtered)
    scale = np.percentile(magnitude, 99)
    peaks, _ = find_peaks(
        magnitude,
        height=0.40 * scale,
        prominence=0.35 * scale,
        distance=ceil(0.25 * sampling_rate),
    )
    rr_seconds = np.diff(peaks) / sampling_rate
    interval_bpm = 60 / rr_seconds
    heart_rate_bpm = float(60 / rr_seconds.mean()) if rr_seconds.size else float("nan")
    return Analysis(filtered, peaks, rr_seconds, interval_bpm, heart_rate_bpm)
