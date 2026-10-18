from agents.incident_response.post_mortem import resolve_fault_title


def test_title_prefers_scenario():
    assert resolve_fault_title({"scenario": "CPU_SATURATION", "fault_type": "OTHER"}) == "CPU_SATURATION"


def test_title_uses_fault_type_when_scenario_missing():
    assert resolve_fault_title({"fault_type": "REDIS_CONNECTION_STARVATION"}) == "REDIS_CONNECTION_STARVATION"


def test_title_uses_vector_as_last_named_fallback():
    assert resolve_fault_title({"vector": "MEMORY_LEAK_OOM"}) == "MEMORY_LEAK_OOM"


def test_title_unknown_when_empty():
    assert resolve_fault_title({}) == "UNKNOWN_FAULT"
