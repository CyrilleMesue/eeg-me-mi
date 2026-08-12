"""Prespecified ROI and spatial-control channel sets.

Frozen before inspecting spatial-control decoding results.
"""

from __future__ import annotations

from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS

# E03 primary ROI summaries
ROI_LEFT = ("FC3", "C3", "CP3")
ROI_RIGHT = ("FC4", "C4", "CP4")
ROI_MIDLINE = ("FCz", "Cz", "CPz")

ROIS: dict[str, tuple[str, ...]] = {
    "left_sensorimotor": ROI_LEFT,
    "right_sensorimotor": ROI_RIGHT,
    "midline": ROI_MIDLINE,
}

# E05 spatial-plausibility control: matched-size (21) non-central / peripheral set.
# Rationale: prefer prefrontal, frontopolar, temporal, occipital, and outer
# parietal sites away from the primary FC/C/CP sensorimotor strip used in E01.
# Chosen from standard 10–05 labels present on EEGMMIDB 64-channel montages.
# Channel count is matched to SENSORIMOTOR_CHANNELS (21). Anatomical limitation:
# scalp EEG cannot guarantee non-overlap of volume-conducted sensorimotor signal.
SPATIAL_CONTROL_CHANNELS: tuple[str, ...] = (
    "Fp1", "Fpz", "Fp2",
    "AF7", "AF3", "AFz", "AF4", "AF8",
    "F7", "F8",
    "FT7", "FT8",
    "T7", "T8",
    "TP7", "TP8",
    "P7", "P8",
    "O1", "Oz", "O2",
)

assert len(SPATIAL_CONTROL_CHANNELS) == len(SENSORIMOTOR_CHANNELS) == 21
assert not set(SPATIAL_CONTROL_CHANNELS) & set(SENSORIMOTOR_CHANNELS), (
    "Spatial-control set must not overlap primary sensorimotor channels"
)


def spatial_control_rationale() -> dict:
    return {
        "name": "peripheral_non_sensorimotor_21",
        "n_channels": len(SPATIAL_CONTROL_CHANNELS),
        "matched_to_primary_count": True,
        "primary_set": list(SENSORIMOTOR_CHANNELS),
        "control_set": list(SPATIAL_CONTROL_CHANNELS),
        "rationale": (
            "Matched-size set of prefrontal/frontopolar, lateral frontal/temporal, "
            "and occipital sites away from the FC/C/CP strip; frozen before control "
            "decoding results were inspected."
        ),
        "anatomical_limitations": (
            "Volume conduction and reference effects mean peripheral channels can "
            "still carry sensorimotor or global-state information; this control "
            "cannot prove cortical origin."
        ),
    }
