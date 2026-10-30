"""Scientific Measurement Provenance Framework (DEF-30).

Standardizes classification of all physical, optical, and kinematic measurements:
- LIVE_MEASURED: Authenticated measurement from calibrated physical sensor/camera.
- SYNTHETIC_TEST: Explicitly synthetic, modeled, or fixture-generated test data.
- NOT_MEASURABLE: Hardware absent, target occluded, or unresolvable sensor capture.
- INVALID_INPUT: Degenerate, out-of-bounds, or ill-conditioned mathematical input.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, Optional


class MeasurementProvenanceType(str, Enum):
    """Rigorous classification of measurement origin."""
    LIVE_MEASURED = "LIVE_MEASURED"
    SYNTHETIC_TEST = "SYNTHETIC_TEST"
    NOT_MEASURABLE = "NOT_MEASURABLE"
    INVALID_INPUT = "INVALID_INPUT"


def build_measurement_provenance(
    provenance_type: MeasurementProvenanceType | str,
    *,
    source: str = "WORKSTATION_RUNTIME",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate standardized scientific provenance metadata block."""
    if isinstance(provenance_type, MeasurementProvenanceType):
        ptype_str = provenance_type.value
    else:
        ptype_str = str(provenance_type).upper()
        if ptype_str not in {e.value for e in MeasurementProvenanceType}:
            ptype_str = MeasurementProvenanceType.INVALID_INPUT.value

    is_live = ptype_str == MeasurementProvenanceType.LIVE_MEASURED.value
    is_synthetic = ptype_str == MeasurementProvenanceType.SYNTHETIC_TEST.value
    is_valid = ptype_str in {
        MeasurementProvenanceType.LIVE_MEASURED.value,
        MeasurementProvenanceType.SYNTHETIC_TEST.value,
    }

    return {
        "provenance_type": ptype_str,
        "is_live_measurement": is_live,
        "is_synthetic": is_synthetic,
        "is_valid": is_valid,
        "source": source,
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "clinical_use_permitted": False,
        "details": details or {},
    }
