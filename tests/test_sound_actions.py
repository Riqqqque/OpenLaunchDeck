from openlaunchdeck.actions.context import ActionContext
from openlaunchdeck.actions.stop_sound import StopSoundAction
from openlaunchdeck.models.button import ButtonConfig
from openlaunchdeck.models.profile import Profile


class FakeAudioEngine:
    def __init__(self):
        self.calls = []

    def stop_button(self, button_id):
        self.calls.append(("button", button_id))

    def stop_page(self, page_id):
        self.calls.append(("page", page_id))

    def stop_all(self):
        self.calls.append(("all", None))


def make_context(audio_engine):
    profile = Profile.blank()
    page = profile.get_page("main")
    return ActionContext(
        logger=None,
        current_profile=profile,
        current_page=page,
        button_id="A1",
        button_config=ButtonConfig.blank("A1"),
        audio_engine=audio_engine,
    )


def test_stop_sound_action_scopes():
    audio_engine = FakeAudioEngine()
    context = make_context(audio_engine)
    action = StopSoundAction()

    assert action.execute(context, {"scope": "this_button"}).success is True
    assert action.execute(context, {"scope": "current_page"}).success is True
    assert action.execute(context, {"scope": "all"}).success is True

    assert audio_engine.calls == [("button", "A1"), ("page", "main"), ("all", None)]
