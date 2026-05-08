#!/usr/bin/python
"""Glide scraper"""

import logging

from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError
from hdx.location.country import Country
from hdx.utilities.dictandlist import dict_of_lists_add
from hdx.utilities.retriever import Retrieve

logger = logging.getLogger(__name__)

_MAINTAINER = "196196be-6037-4488-8b71-d786adf4c081"
_OWNER_ORG = "ebcfe377-bad0-46d0-b68f-cca8e6b54e33"
_EXCLUDED_FIELDS = frozenset({"features", "id", "idsource", "time"})
_HEADERS = [
    "glidenumber", "number", "docid", "event", "geocode",
    "location", "latitude", "longitude", "latitude2", "longitude2",
    "shape_type", "year", "month", "day", "time",
    "status", "killed", "injured", "homeless", "affected",
    "magnitude", "duration", "comments", "source",
    "id", "idsource", "features",
]


class Pipeline:
    def __init__(
        self,
        configuration: Configuration,
        retriever: Retrieve,
        today,
        folder: str,
    ):
        self._configuration = configuration
        self._retriever = retriever
        self._today = today
        self._folder = folder
        self._events = {}
        self._country_startdate = {}
        self._country_enddate = {}
        self._headers = None

    def get_countriesdata(self) -> list[dict]:
        url = self._configuration["url"]
        json_data = self._retriever.download_json(url, "glide.json")
        glideset = json_data["glideset"]
        min_year = self._today.year - 1

        for event in glideset:
            year = event.get("year") or 0
            if year < min_year:
                continue
            geocode = event.get("geocode", "")
            if not geocode or len(geocode) != 3:
                continue

            month = event.get("month") or 1
            day = event.get("day") or 1
            event_date = f"{year:04d}-{month:02d}-{day:02d}"

            existing_min = self._country_startdate.get(geocode)
            if not existing_min or event_date < existing_min:
                self._country_startdate[geocode] = event_date
            existing_max = self._country_enddate.get(geocode)
            if not existing_max or event_date > existing_max:
                self._country_enddate[geocode] = event_date

            clean_event = {k: v for k, v in event.items() if k not in _EXCLUDED_FIELDS}
            dict_of_lists_add(self._events, geocode, clean_event)

        if not self._events:
            raise ValueError(f"No countries with events since {min_year}")

        self._headers = [h for h in _HEADERS if h not in _EXCLUDED_FIELDS]

        return [{"iso3": iso3} for iso3 in sorted(self._events)]

    def generate_dataset_and_showcase(self, countryiso: str) -> tuple:
        countryname = Country.get_country_name_from_iso3(countryiso)
        if not countryname:
            logger.warning(f"No country name for {countryiso}, skipping")
            return None, None, False

        countryiso_lower = countryiso.lower()
        name = f"{countryiso_lower}-glide-events"
        title = f"{countryname} - GLIDE Disaster Events"
        dataset = Dataset({"name": name, "title": title})
        try:
            dataset.add_country_location(countryiso)
        except HDXError:
            logger.error(f"Couldn't find country {countryiso}, skipping")
            return None, None, False

        if countryiso not in self._events:
            return dataset, None, False

        dataset.set_maintainer(_MAINTAINER)
        dataset.set_organization(_OWNER_ORG)
        dataset.set_expected_update_frequency("Every week")
        dataset.set_time_period(
            self._country_startdate[countryiso],
            self._country_enddate[countryiso],
        )
        dataset.set_subnational(True)

        rows = self._events[countryiso]
        event_types = self._configuration["event_types"]
        tags = set()
        for row in rows:
            event_code = row.get("event", "")
            if event_code in event_types:
                tags.add(event_types[event_code])
        dataset.add_tags(sorted(tags))

        filename = f"{countryiso_lower}_glide_events.csv"
        resourcedata = {
            "name": filename,
            "description": f"GLIDE disaster events for {countryname}",
        }
        dataset.generate_resource(
            self._folder,
            filename,
            rows,
            resourcedata,
            headers=self._headers,
            no_empty=False,
        )
        return dataset, None, True
