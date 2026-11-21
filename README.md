# ECG beat detection and heart-rate analysis

## Setup and run

From the project root, create an environment and install the pinned direct dependencies. The baseline was run with Python 3.14.

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the public-record benchmark and regenerate both outputs.

```sh
python -m ecg
```

The command reads the record from PhysioNet and writes `outputs/metrics.csv` and `outputs/ecg_segment.png`. The figure shows seconds 5–15. The CSV covers the full recording. If PhysioNet is unreachable, append `--synthetic` to check the pipeline with a seeded 30-second simulated signal and known beat positions. That run writes to `outputs/synthetic/` by default. Use `--output-dir PATH` to choose a different destination.

## Recording and reference

The [MIT-BIH Arrhythmia Database v1.0.0](https://physionet.org/content/mitdb/1.0.0/) is a public collection of annotated ambulatory ECG excerpts. This project uses [record 100, channel MLII](https://physionet.org/files/mitdb/1.0.0/100.hea), sampled at 360 Hz and read in mV. Its `atr` reference beat symbols are `N` (normal), `A` (atrial premature), and `V` (premature ventricular). All three are included. Other annotations, such as `+` for a rhythm change, are excluded. The symbol list is specific to this record. [PhysioNet record directory](https://physionet.org/files/mitdb/1.0.0/mitdbdir/records.htm)

## Processing

Call `ecg.processing.analyze_ecg(signal, sampling_rate)` with a finite, evenly sampled, one-dimensional signal and its rate in Hz. It returns the filtered waveform, detected sample indices, RR intervals in seconds, per-interval rates, and a recording-level rate. The function accepts samples from any recording source. The recording and annotation loader lives in `ecg.recording`.

- The filter is a 5–20 Hz Butterworth bandpass with order 3 per band edge. Second-order sections are applied forward and backward for zero phase shift. This attenuates baseline drift and high-frequency noise while emphasizing QRS deflections. The sampling rate must exceed 40 Hz and the signal must contain more than 21 samples.
- The detector finds local maxima of the absolute filtered signal so it can detect either polarity. It uses the 99th percentile of the magnitude as a scale. Minimum height is 40% of this scale and minimum prominence is 35%. Candidates must be at least 250 ms apart, rounded up to a whole sample. When candidates are closer, the larger peak takes priority.
- Each pair of consecutive detections gives an RR interval. Per-interval rate is 60 divided by that interval in seconds. The CSV reports 60 divided by the mean RR interval across all detections. With fewer than two detections the CSV rate is blank.

## Evaluation

The evaluator includes every sample, including the filter edges. Duration is the number of samples divided by the sampling rate. Matching walks both sorted beat lists, consumes the earliest feasible pair within an inclusive ±100 ms (36 samples at 360 Hz), and skips the earlier beat when the gap exceeds the tolerance. Each beat can be used once. This maximizes the match count and can pair with an earlier eligible beat when several are available. Misses and extras are the unmatched reference and detected beats, respectively. Precision is matches divided by detections and recall is matches divided by reference beats. A zero denominator produces a blank CSV field. Reference indices are used only for scoring and plotting.

This single-record, single-lead baseline has no independent validation. Record 100 is predominantly normal beats, so the scores give limited evidence about other leads, morphologies, noise conditions, or hardware recordings. Match counts measure agreement within the tolerance and do not quantify timing error. The recording-level rate pools all detected intervals, including any affected by detection errors. Forward/backward filtering and the recording-wide percentile require a batch of samples. Rhythm classification is deferred.
