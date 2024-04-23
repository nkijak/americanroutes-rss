from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from crawler import parser
import pytest


TZINFO = ZoneInfo("America/New_York")


# TODO freezegun to keep date in 2024
def test_parse_year():
    with open("tests/data/year.html", "rb") as html:
        data = html.read()

    actual = parser.__parse_year(data)
    expected = [
        f"https://amroutes.org{link}"
        for link in ["/blog-3-1", "/feb-2024", "/march-2024", "/april-2024"]
    ]

    assert actual == expected


def test_parse_month():
    with open("tests/data/month.html") as html:
        actual = parser.parse_month(html)
    expected = [
        "https://amroutes.org/march-2024/blog-post-title-one-dae5b-7txxs-r522b-k9ggb-2nwpd-5xxmj-zmwdy-gd6fr",
        "https://amroutes.org/march-2024/blog-post-title-one-dae5b-7txxs-r522b-k9ggb-2nwpd-5xxmj-zmwdy",
        "https://amroutes.org/march-2024/blog-post-title-one-dae5b-7txxs-r522b-k9ggb-2nwpd-5xxmj",
        "https://amroutes.org/march-2024/blog-post-title-one-dae5b-7txxs-r522b-k9ggb-2nwpd",
    ]
    assert actual == expected


def test_parse_episodes():
    with open("tests/data/show.html") as html:
        actual = parser.parse_episodes(html.read())
    description = "Easter weekend is a time for reflection and family, and our guests certainly fit the bill. Donald Harrison, Jr. is a saxophone player and New Orleans native. Harrison’s ties to New Orleans run deep, musically and culturally. Wendell and Sherman Holmes, plus longtime friend Popsy Dixon made up the Holmes Brothers, a vocal group best known for putting their personal stamp on blues, gospel, country, pop and more. We revisit our conversation with the brothers about the transition from Christ Church, Virginia to New York and back again to home and family."
    url = "https://www.amroutes.org/march-2024/blog-post-title-one-dae5b-7txxs-r522b-k9ggb-2nwpd-5xxmj-zmwdy-gd6fr"
    assert actual == [
        parser.Episode(
            "EASTER WITH DONALD HARRISON, JR. AND HOLMES BROTHERS",
            description=description,
            date=datetime(2024, 3, 27, 1, tzinfo=TZINFO),
            media_url="https://static1.squarespace.com/static/6608b67820a1e41cb804e883/t/661462d1874dbd05be7c70a1/1712612173403/2413_01.mp3/original/2413_01.mp3",
            url=url,
            hour=1,
        ),
        parser.Episode(
            "EASTER WITH DONALD HARRISON, JR. AND HOLMES BROTHERS",
            description=description,
            date=datetime(2024, 3, 27, 2, tzinfo=TZINFO),
            media_url="https://static1.squarespace.com/static/6608b67820a1e41cb804e883/t/661463743c3afb2d49e2c0d4/1712612330757/2413_02.mp3/original/2413_02.mp3",
            url=url,
            hour=2,
        ),
    ]


def test_old_guid_generation():
    eps = parser.Episode(
        "title",
        description="whatever",
        date=datetime(2024, 2, 21, 2, tzinfo=TZINFO),
        media_url="https://static1.squarespace.com/static/6608b67820a1e41cb804e883/t/661463743c3afb2d49e2c0d4/1712612330757/2413_02.mp3/original/2413_02.mp3",
        url="whatever",
        hour=2,
    )
    expected = "https://americanroutes.s3.amazonaws.com/shows/2413_02.mp3"
    assert eps.guid() == expected


# TODO test caching of fetch method
@pytest.mark.skip("Replace this with __fetch_content cache test")
def test_show_details_cache():
    actual = parser.show_details(
        Path("tests"), "https://whatever/archives/data/show_detail.json", 1
    )
    expected = parser.Episode(
        "Making Music on Records & Excavating Shellac",
        description="We're spinning jazz, country, blues, pop and roots music heard locally and globally for over a century on records and later on jukeboxes, in cafes, barrooms and juke joints. We'll hear June Carter and Johnny Cash, New Orleans' jazzmen Kermit Ruffins and Danny Barker, Robert Johnson, and the Rolling Stones...then and now. Plus we'll travel the world from earlier in the 20th century in search of rare music on 78s as dug up by sonic researcher, <b>Jonathan Ward</b>, for his collection, \"Excavated Shellac: An Alternate History of the Worlds Music.\"\n",
        date=datetime(2024, 1, 24, 1, tzinfo=TZINFO),
        media_url="https://americanroutes.s3.amazonaws.com/shows/2404_01.mp3",
        url="http://americanroutes.wwno.org/archives/show/1368/",
    )
    assert actual == expected
