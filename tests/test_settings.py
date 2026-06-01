from openlaunchdeck.models.settings import Settings


def test_settings_grid_density_defaults_and_validation():
    assert Settings.from_dict({}).grid_density == "comfortable"
    assert Settings.from_dict({"grid_density": "compact"}).grid_density == "compact"
    assert Settings.from_dict({"grid_density": "huge"}).grid_density == "comfortable"
