import json
import requests
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from crawler import parser

TZINFO = ZoneInfo("America/New_York")


def test_detail_links(tmp_path: Path):
    with open("tests/data/archives.html") as html:
        actual = parser.parse_detail_links(html)
    assert len(actual) == 5


def test_parse_archive_episode(tmp_path: Path):
    with open("tests/data/archives.html") as html:
        archives = parser.parse_detail_links(html)
    actual = archives[0]
    expected = [
        "http://americanroutes.wwno.org/archives/show_data/1369/1",
        "http://americanroutes.wwno.org/archives/show_data/1369/2",
    ]
    assert actual == expected


def test_parse_show_details():
    with open("tests/data/show_detail.json") as raw:
        details = json.load(raw)
    actual = parser.parse_show_details(details, 1)
    expected = parser.Episode(
        "Making Music on Records & Excavating Shellac",
        description="We're spinning jazz, country, blues, pop and roots music heard locally and globally for over a century on records and later on jukeboxes, in cafes, barrooms and juke joints. We'll hear June Carter and Johnny Cash, New Orleans' jazzmen Kermit Ruffins and Danny Barker, Robert Johnson, and the Rolling Stones...then and now. Plus we'll travel the world from earlier in the 20th century in search of rare music on 78s as dug up by sonic researcher, <b>Jonathan Ward</b>, for his collection, \"Excavated Shellac: An Alternate History of the Worlds Music.\"\n",
        date=datetime(2024, 1, 24, tzinfo=TZINFO),
        media_url="https://americanroutes.s3.amazonaws.com/shows/2404_01.mp3",
        url="http://americanroutes.wwno.org/archives/show/1368/",
    )
    assert actual == expected


def test_show_details_cache():
    actual = parser.show_details(
        Path("tests"), "https://whatever/archives/data/show_detail.json", 1
    )
    expected = parser.Episode(
        "Making Music on Records & Excavating Shellac",
        description="We're spinning jazz, country, blues, pop and roots music heard locally and globally for over a century on records and later on jukeboxes, in cafes, barrooms and juke joints. We'll hear June Carter and Johnny Cash, New Orleans' jazzmen Kermit Ruffins and Danny Barker, Robert Johnson, and the Rolling Stones...then and now. Plus we'll travel the world from earlier in the 20th century in search of rare music on 78s as dug up by sonic researcher, <b>Jonathan Ward</b>, for his collection, \"Excavated Shellac: An Alternate History of the Worlds Music.\"\n",
        date=datetime(2024, 1, 24, tzinfo=TZINFO),
        media_url="https://americanroutes.s3.amazonaws.com/shows/2404_01.mp3",
        url="http://americanroutes.wwno.org/archives/show/1368/",
    )
    assert actual == expected


def test_show_details_fetch(monkeypatch, tmp_path):
    with open("tests/data/show_detail.json") as raw:
        details = json.load(raw)

    def mockresponse(*args, **kwargs):
        response = requests.Response()
        response._content = str.encode(json.dumps(details))
        response.status_code = 200
        return response

    monkeypatch.setattr(requests, "get", mockresponse)
    actual = parser.show_details(
        tmp_path, "https://whatever/archives/data/show_detail.json", 1
    )
    expected = parser.Episode(
        "Making Music on Records & Excavating Shellac",
        description="We're spinning jazz, country, blues, pop and roots music heard locally and globally for over a century on records and later on jukeboxes, in cafes, barrooms and juke joints. We'll hear June Carter and Johnny Cash, New Orleans' jazzmen Kermit Ruffins and Danny Barker, Robert Johnson, and the Rolling Stones...then and now. Plus we'll travel the world from earlier in the 20th century in search of rare music on 78s as dug up by sonic researcher, <b>Jonathan Ward</b>, for his collection, \"Excavated Shellac: An Alternate History of the Worlds Music.\"\n",
        date=datetime(2024, 1, 24, tzinfo=TZINFO),
        media_url="https://americanroutes.s3.amazonaws.com/shows/2404_01.mp3",
        url="http://americanroutes.wwno.org/archives/show/1368/",
    )
    assert actual == expected
    expected_file = tmp_path / "data" / "show_detail.json"
    assert expected_file.exists
    with open(expected_file) as actual_data:
        assert json.load(actual_data) == details
