from hdx.utilities.compare import assert_files_same
from hdx.utilities.dateparse import parse_date
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from hdx.scraper.glide.pipeline import Pipeline


class TestGlide:
    afg_dataset = {
        "data_update_frequency": "-2",
        "dataset_date": "[2025-03-15T00:00:00 TO 2025-04-20T23:59:59]",
        "groups": [{"name": "afg"}],
        "maintainer": "196196be-6037-4488-8b71-d786adf4c081",
        "name": "afg-glide-events",
        "owner_org": "ebcfe377-bad0-46d0-b68f-cca8e6b54e33",
        "subnational": "1",
        "tags": [
            {
                "name": "earthquake-tsunami",
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
            },
            {
                "name": "flooding",
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
            },
            {
                "name": "natural disasters",
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
            },
        ],
        "title": "Afghanistan - GLIDE Disaster Events",
    }
    afg_resource = {
        "description": "GLIDE disaster events for Afghanistan",
        "format": "csv",
        "name": "afg_glide_events.csv",
    }
    sdn_dataset = {
        "groups": [{"name": "sdn"}],
        "name": "sdn-glide-events",
        "title": "Sudan - GLIDE Disaster Events",
    }

    def test_generate_dataset_and_showcase(
        self, configuration, fixtures_dir, input_dir, config_dir
    ):
        with temp_dir(
            "TestGlide", delete_on_success=True, delete_on_failure=False
        ) as tempdir:
            with Download(user_agent="test") as downloader:
                retriever = Retrieve(
                    downloader=downloader,
                    fallback_dir=tempdir,
                    saved_dir=input_dir,
                    temp_dir=tempdir,
                    save=False,
                    use_saved=True,
                )
                today = parse_date("2026-05-07")
                pipeline = Pipeline(configuration, retriever, today, tempdir)
                countries = pipeline.get_countriesdata()
                # Only AFG has events in year >= 2025; the 2024 event is filtered out
                assert len(countries) == 1

                dataset, showcase, populated = pipeline.generate_dataset_and_showcase(
                    "AFG"
                )
                assert dataset == self.afg_dataset
                assert showcase is None
                assert populated is True
                resources = dataset.get_resources()
                assert resources[0] == self.afg_resource

                # Country with no events in the time window
                dataset, showcase, populated = pipeline.generate_dataset_and_showcase(
                    "SDN"
                )
                assert dataset == self.sdn_dataset
                assert showcase is None
                assert populated is False
                assert len(dataset.get_resources()) == 0

                filename = "afg_glide_events.csv"
                assert_files_same(fixtures_dir / filename, tempdir / filename)