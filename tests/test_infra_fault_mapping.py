from agents.fault_injector.infra_disruptor import resolve_infra_fault_kind


def test_redis_starvation_is_not_memory_leak():
    assert resolve_infra_fault_kind("REDIS_CONNECTION_STARVATION") == "REDIS_CONNECTION_STARVATION"
    assert resolve_infra_fault_kind("redis-starvation") == "REDIS_CONNECTION_STARVATION"


def test_cpu_and_crash_and_default():
    assert resolve_infra_fault_kind("CPU_SATURATION") == "CPU_SATURATION"
    assert resolve_infra_fault_kind("PROCESS_CRASH") == "PROCESS_CRASH"
    assert resolve_infra_fault_kind("MEMORY_EXHAUSTION") == "MEMORY_EXHAUSTION"
    assert resolve_infra_fault_kind("UNKNOWN") == "MEMORY_EXHAUSTION"
