from openlaunchdeck.actions.base import ActionResult


def test_ok_sets_lighting_flag_separately_from_details():
    result = ActionResult.ok("Sound started.", should_update_lighting=True, source="sound")

    assert result.success is True
    assert result.message == "Sound started."
    assert result.should_update_lighting is True
    assert result.details == {"source": "sound"}


def test_fail_sets_lighting_flag_separately_from_details():
    result = ActionResult.fail("Action failed.", should_update_lighting=True, reason="timeout")

    assert result.success is False
    assert result.message == "Action failed."
    assert result.should_update_lighting is True
    assert result.details == {"reason": "timeout"}
