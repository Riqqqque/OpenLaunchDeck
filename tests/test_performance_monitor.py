from openlaunchdeck.services.performance_monitor import PerformanceMonitor


def test_performance_monitor_records_when_enabled():
    monitor = PerformanceMonitor(enabled=True)

    with monitor.measure("unit_test"):
        pass

    samples = monitor.samples()
    assert len(samples) == 1
    assert samples[0].label == "unit_test"
    assert samples[0].elapsed_ms >= 0


def test_performance_monitor_is_quiet_by_default():
    monitor = PerformanceMonitor(enabled=False)

    monitor.record("quiet", 1.0)

    assert monitor.samples() == []


def test_performance_monitor_record_since_returns_elapsed():
    monitor = PerformanceMonitor(enabled=True)
    start = monitor.now()

    elapsed = monitor.record_since("since", start, area="test")

    assert elapsed >= 0
    assert monitor.samples()[0].details["area"] == "test"
