"""Unit tests for surface-registration-v1 benchmark suite (SR-01..SR-10)."""

from msk_research_lab.benchmarks.surface_registration import SurfaceRegistrationBenchmark


def test_surface_registration_all_cases_pass():
    benchmark = SurfaceRegistrationBenchmark()
    res = benchmark.run_all(method_name="test_reference_geometry")

    assert res["suite"] == "surface-registration-v1"
    assert res["total_cases"] == 10
    assert res["passed"] == 10
    assert res["failed"] == 0
    assert res["overall_status"] == "PASS"

    case_ids = [c["case_id"] for c in res["cases"]]
    assert case_ids == [f"SR-{str(i).zfill(2)}" for i in range(1, 11)]

    # Check determinism case
    sr10 = next(c for c in res["cases"] if c["case_id"] == "SR-10")
    assert sr10["status"] == "PASS"
