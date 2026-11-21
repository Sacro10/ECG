"""Load the public benchmark or generate a deterministic smoke-test input."""

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np


@dataclass
class Recording:
    signal: np.ndarray
    sampling_rate: float
    reference: np.ndarray
    dataset: str
    record_id: str
    lead: str
    units: str


def load_record_100() -> Recording:
    import requests
    import wfdb

    base_url = "https://physionet.org/files/mitdb/1.0.0"
    with TemporaryDirectory() as directory, requests.Session() as session:
        for extension in ("hea", "dat", "atr"):
            filename = f"100.{extension}"
            response = session.get(f"{base_url}/{filename}", timeout=20)
            response.raise_for_status()
            (Path(directory) / filename).write_bytes(response.content)
        record_path = str(Path(directory) / "100")
        record = wfdb.rdrecord(record_path, channel_names=["MLII"])
        annotation = wfdb.rdann(record_path, "atr")
    beat_mask = np.isin(annotation.symbol, ("N", "A", "V"))
    return Recording(
        record.p_signal[:, 0], float(record.fs), annotation.sample[beat_mask],
        "MIT-BIH Arrhythmia Database v1.0.0", "100", "MLII", record.units[0],
    )


def synthetic_recording() -> Recording:
    fs = 360.0
    time = np.arange(int(30 * fs)) / fs
    reference = np.arange(360, int(29 * fs), 288)
    signal = 0.10 * np.sin(2 * np.pi * 0.35 * time)
    signal += np.random.default_rng(42).normal(0, 0.02, time.size)
    for peak in reference:
        offset = time - peak / fs
        signal += np.exp(-0.5 * (offset / 0.015)**2)
        signal += 0.24 * np.exp(-0.5 * ((offset - 0.24) / 0.055)**2)
    return Recording(signal, fs, reference, "Synthetic smoke test", "synthetic", "simulated", "a.u.")
