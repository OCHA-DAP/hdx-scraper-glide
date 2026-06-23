import json

from hdx.utilities.compare import assert_files_same
from hdx.utilities.dateparse import parse_date
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from hdx.scraper.glide.pipeline import Pipeline


class TestGlide:
    afg_dataset = {
        "data_update_frequency": "-2",
        "dataset_date": "[2023-11-01T00:00:00 TO 2025-04-20T23:59:59]",
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
    afg_geojson_resource = {
        "description": "GLIDE disaster events GeoJSON for Afghanistan",
        "format": "geojson",
        "name": "afg_glide_events.geojson",
    }
    sdn_dataset = {
        "groups": [{"name": "sdn"}],
        "name": "sdn-glide-events",
        "title": "Sudan - GLIDE Disaster Events",
    }
    global_dataset = {
        "data_update_frequency": "-2",
        "dataset_date": "[2023-11-01T00:00:00 TO 2025-04-20T23:59:59]",
        "groups": [{"name": "world"}],
        "maintainer": "196196be-6037-4488-8b71-d786adf4c081",
        "name": "global-glide-events",
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
        "title": "Global - GLIDE Disaster Events",
    }
    global_resource = {
        "description": "GLIDE disaster events for all countries",
        "format": "csv",
        "name": "glide_events_global.csv",
    }
    global_geojson_resource = {
        "description": "GLIDE disaster events GeoJSON for all countries",
        "format": "geojson",
        "name": "glide_events_global.geojson",
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
                assert len(countries) == 1

                dataset, showcase, populated = pipeline.generate_dataset_and_showcase(
                    "AFG"
                )
                assert dataset == self.afg_dataset
                assert showcase is None
                assert populated is True
                resources = dataset.get_resources()
                assert resources[0] == self.afg_resource
                assert resources[1] == self.afg_geojson_resource

                # Country with no events in the time window
                dataset, showcase, populated = pipeline.generate_dataset_and_showcase(
                    "SDN"
                )
                assert dataset == self.sdn_dataset
                assert showcase is None
                assert populated is False
                assert len(dataset.get_resources()) == 0

                assert_files_same(
                    fixtures_dir / "afg_glide_events.csv",
                    tempdir / "afg_glide_events.csv",
                )
                assert_files_same(
                    fixtures_dir / "afg_glide_events.geojson",
                    tempdir / "afg_glide_events.geojson",
                )

    def test_generate_global_dataset(
        self, configuration, fixtures_dir, input_dir, config_dir
    ):
        with temp_dir(
            "TestGlideGlobal", delete_on_success=True, delete_on_failure=False
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
                pipeline.get_countriesdata()

                dataset = pipeline.generate_global_dataset()
                assert dataset == self.global_dataset
                resources = dataset.get_resources()
                assert resources[0] == self.global_resource
                assert resources[1] == self.global_geojson_resource

                assert_files_same(
                    fixtures_dir / "glide_events_global.csv",
                    tempdir / "glide_events_global.csv",
                )
                assert_files_same(
                    fixtures_dir / "glide_events_global.geojson",
                    tempdir / "glide_events_global.geojson",
                )

    def test_invalid_dates(self, configuration, tmp_path):
        # day=0 in April 2025 → clamped to 2025-04-01 (recent, triggers country_has_recent)
        # day=31 in April 1998 → clamped to 1998-04-30 (April has 30 days)
        glide_data = {
            "glideset": [
                {
                    "glidenumber": "FL-2025-000099-AFG",
                    "number": "2025-000099",
                    "docid": 9001,
                    "event": "FL",
                    "geocode": "AFG",
                    "year": 2025,
                    "month": 4,
                    "day": 0,
                    "time": "",
                    "location": "Kabul",
                    "latitude": 34.5,
                    "longitude": 69.2,
                    "latitude2": 0.0,
                    "longitude2": 0.0,
                    "shape_type": 0,
                    "status": "A",
                    "killed": 0,
                    "injured": 0,
                    "homeless": 0,
                    "affected": 0,
                    "duration": 0,
                    "magnitude": "",
                    "source": "",
                    "comments": "",
                    "id": "",
                    "idsource": "",
                    "features": [],
                },
                {
                    "glidenumber": "FL-1998-000001-AFG",
                    "number": "1998-000001",
                    "docid": 9002,
                    "event": "FL",
                    "geocode": "AFG",
                    "year": 1998,
                    "month": 4,
                    "day": 31,
                    "time": "",
                    "location": "Kabul",
                    "latitude": 34.5,
                    "longitude": 69.2,
                    "latitude2": 0.0,
                    "longitude2": 0.0,
                    "shape_type": 0,
                    "status": "A",
                    "killed": 0,
                    "injured": 0,
                    "homeless": 0,
                    "affected": 0,
                    "duration": 0,
                    "magnitude": "",
                    "source": "",
                    "comments": "",
                    "id": "",
                    "idsource": "",
                    "features": [],
                },
            ]
        }
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "glide.json").write_text(json.dumps(glide_data))
        empty_geojson = json.dumps({"type": "FeatureCollection", "features": []})
        (input_dir / "glide_afg.geojson").write_text(empty_geojson)
        (input_dir / "glide_global.geojson").write_text(empty_geojson)

        with Download(user_agent="test") as downloader:
            retriever = Retrieve(
                downloader=downloader,
                fallback_dir=tmp_path,
                saved_dir=input_dir,
                temp_dir=tmp_path,
                save=False,
                use_saved=True,
            )
            today = parse_date("2026-05-07")
            pipeline = Pipeline(configuration, retriever, today, tmp_path)
            countries = pipeline.get_countriesdata()

        assert countries == [{"iso3": "AFG"}]
        assert len(pipeline._events["AFG"]) == 2
        assert pipeline._country_startdate["AFG"] == parse_date("1998-04-30")
        assert pipeline._country_enddate["AFG"] == parse_date("2025-04-01")
