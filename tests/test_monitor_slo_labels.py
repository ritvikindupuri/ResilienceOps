from agents.incident_response.monitor import probe_error_rate_percent
from agents.incident_response.post_mortem import resolve_fault_title


def test_probe_error_rate_from_health_statuses():
    snapshot = {"gateway_status": 200, "order_status": 503, "payment_status": 200}
    assert abs(probe_error_rate_percent(snapshot) - (100.0 / 3.0)) < 1e-9


def test_fault_and_scenario_alignment_example():
    event = {"fault_type": "REDIS_CONNECTION_STARVATION"}
    assert resolve_fault_title(event) != "UNKNOWN_FAULT"
