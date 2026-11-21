"""One-to-one benchmark matching on sorted sample indices."""


def count_matches(detected, reference, tolerance_samples: int) -> int:
    """Count a maximum-cardinality match using the earliest feasible pair."""
    detection_index = reference_index = matched = 0
    while detection_index < len(detected) and reference_index < len(reference):
        difference = detected[detection_index] - reference[reference_index]
        if difference < -tolerance_samples:
            detection_index += 1
        elif difference > tolerance_samples:
            reference_index += 1
        else:
            matched += 1
            detection_index += 1
            reference_index += 1
    return matched
