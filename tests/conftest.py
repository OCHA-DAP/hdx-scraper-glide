from os.path import join
from pathlib import Path

import pytest
from hdx.api.configuration import Configuration
from hdx.api.locations import Locations
from hdx.data.vocabulary import Vocabulary
from hdx.location.country import Country
from hdx.utilities.useragent import UserAgent


@pytest.fixture(scope="session")
def fixtures_dir():
    return Path("tests") / "fixtures"


@pytest.fixture(scope="session")
def input_dir(fixtures_dir):
    return fixtures_dir / "input"


@pytest.fixture(scope="session")
def config_dir():
    return Path("src") / "hdx" / "scraper" / "glide" / "config"


@pytest.fixture(scope="session")
def configuration(config_dir):
    UserAgent.set_global("test")
    Configuration._create(
        hdx_read_only=True,
        hdx_site="prod",
        project_config_yaml=join(config_dir, "project_configuration.yaml"),
    )
    Locations.set_validlocations(
        [
            {"name": "afg", "title": "Afghanistan"},
            {"name": "sdn", "title": "Sudan"},
        ]
    )
    Country.countriesdata(False)
    glide_tags = [
        "agriculture-livestock",
        "climate hazards",
        "complex emergency-conflict-security",
        "cyclones-hurricanes-typhoons",
        "disease",
        "drought",
        "earthquake-tsunami",
        "epidemics-outbreaks",
        "flooding",
        "food security",
        "hazards and risk",
        "health",
        "malnutrition",
        "natural disasters",
    ]
    Vocabulary._tags_dict = {tag: {"Action to Take": "ok"} for tag in glide_tags}
    Vocabulary._approved_vocabulary = {
        "tags": [{"name": tag} for tag in glide_tags],
        "id": "b891512e-9516-4bf5-962a-7a289772a2a1",
        "name": "approved",
    }
    return Configuration.read()
