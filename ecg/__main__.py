"""Run the benchmark and write the figure and metrics."""

import argparse
import csv
from math import floor
from pathlib import Path

import matplotlib
import numpy as np

from .evaluation import count_matches
from .processing import analyze_ecg
from .recording import load_record_100, synthetic_recording

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def save_figure(record, result, path: Path) -> None:
    fs = record.sampling_rate
    start = round(5 * fs)
    stop = min(round(15 * fs), len(record.signal))
    samples = np.arange(start, stop)
    detected = result.peaks[(result.peaks >= start) & (result.peaks < stop)]
    reference = record.reference[(record.reference >= start) & (record.reference < stop)]

    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(12, 5.5), layout="constrained")
    fig.suptitle(f"{record.dataset} · Record {record.record_id} · {record.lead}")
    for ax, signal, label in zip(
        axes, (record.signal, result.filtered), ("Raw ECG", "Filtered ECG (5–20 Hz)")
    ):
        ax.plot(samples / fs, signal[samples], color="#293747", lw=1, label=label)
        ax.scatter(reference / fs, signal[reference], marker="o", s=80,
                   facecolors="none", edgecolors="#0067a5", linewidths=1.4,
                   label="Reference beat", zorder=3)
        ax.scatter(detected / fs, signal[detected], marker="x", s=33,
                   color="#b94200", linewidths=1.5, label="Detected peak", zorder=4)
        ax.set_ylabel(f"Amplitude ({record.units})")
        ax.grid(alpha=0.22)
        ax.legend(loc="upper right", ncols=3, fontsize=9)
        ax.margins(y=0.22)
    axes[-1].set_xlabel("Time from start of recording (s)")
    axes[-1].set_xlim(start / fs, stop / fs)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", action="store_true", help="Run an offline smoke test.")
    parser.add_argument("--output-dir", type=Path, help="Override the default output directory.")
    args = parser.parse_args()
    record = synthetic_recording() if args.synthetic else load_record_100()
    result = analyze_ecg(record.signal, record.sampling_rate)

    tolerance_seconds = 0.10
    tolerance_samples = floor(tolerance_seconds * record.sampling_rate)
    matched = count_matches(result.peaks, record.reference, tolerance_samples)
    detected_count = len(result.peaks)
    reference_count = len(record.reference)
    metrics = {
        "dataset": record.dataset,
        "record_id": record.record_id,
        "lead": record.lead,
        "sampling_rate_hz": record.sampling_rate,
        "evaluated_duration_s": len(record.signal) / record.sampling_rate,
        "tolerance_ms": tolerance_seconds * 1000,
        "tolerance_samples": tolerance_samples,
        "reference_beats": reference_count,
        "detected_beats": detected_count,
        "matched_beats": matched,
        "missed_beats": reference_count - matched,
        "extra_detections": detected_count - matched,
        "precision": matched / detected_count if detected_count else "",
        "recall": matched / reference_count if reference_count else "",
        "estimated_heart_rate_bpm": result.heart_rate_bpm if result.rr_seconds.size else "",
    }

    output = args.output_dir or Path("outputs/synthetic" if args.synthetic else "outputs")
    output.mkdir(parents=True, exist_ok=True)
    save_figure(record, result, output / "ecg_segment.png")
    with (output / "metrics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=metrics)
        writer.writeheader()
        writer.writerow(metrics)
    print(f"Wrote {output / 'ecg_segment.png'} and {output / 'metrics.csv'}")


if __name__ == "__main__":
    main()
