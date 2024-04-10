import datetime
import json
from dataclasses import dataclass
from zoneinfo import ZoneInfo
from typing import List
from pathlib import Path

import requests
from dateutil.parser import parse as date_parse
from bs4.element import Tag
from bs4 import BeautifulSoup
from tqdm import tqdm


# FIXME file length in bytes, reporting as zero even when in files
@dataclass
class Episode:
    title: str
    description: str
    date: datetime.date
    media_url: str
    url: str
    hour: int = 1
    media_size_bytes: int = 0


def latest_episodes(html: str):
    soup = BeautifulSoup(html, "html.parser")
    tracks = soup.find("ul", "list-streams").find_all("li")
    return [t.find("a")["href"] for t in tracks]


def parse_archive_episode(tag: Tag) -> List[str]:
    links = tag.find("div", "list-articles").find_all("a", "js-track-loader")
    return [
        f"http://americanroutes.wwno.org/archives/show_data/{id['data-id']}/{hour+1}"
        for hour, id in enumerate(links)
    ]


def parse_detail_links(html: str) -> List[List[str]]:
    soup = BeautifulSoup(html, "html.parser")
    return [
        parse_archive_episode(details)
        for details in soup.find_all("div", "artist-details")
    ]


def parse_archives(html: str, cachedir: Path) -> List[Episode]:
    retval = []
    for links in tqdm(parse_detail_links(html), desc="Details"):
        hour1, hour2 = links
        retval.append(show_details(cachedir, hour1, 1))
        retval.append(show_details(cachedir, hour2, 2))
    return retval


def parse_show_details(json, hour: int) -> Episode:
    date = date_parse(
        json.get("date"),
        default=datetime.datetime.now(tz=ZoneInfo("America/New_York")).replace(
            hour=hour,
            minute=0,
            second=0,
            microsecond=0,
        ),
    )
    file_url = json.get("abs_file")
    if file_url.endswith("/"):
        file_url = f'https://americanroutes.s3.amazonaws.com/shows/{json.get("show_id").replace("-","")}_0{hour}.mp3'

    return Episode(
        json.get("title"),
        json.get("description"),
        date,
        file_url,
        f'http://americanroutes.wwno.org{json.get("link")}',
        hour,
        json.get("content_length", 0),
    )


def get_size(abs_file_url: str | None) -> int:
    if not abs_file_url:
        return 0
    resp = requests.head(abs_file_url)
    return resp.headers.get("Content-Length", 0)


def show_details(cachedir: Path, show_url: str, hour: int) -> Episode:
    host, show_path = show_url.split("archives/")
    show_file = cachedir / show_path
    if show_file.exists():
        with open(show_file) as raw:
            details = json.load(raw)

    else:
        response = requests.get(show_url)
        response.raise_for_status()
        details = response.json()
        show_file.parent.mkdir(parents=True, exist_ok=True)
        details["content_length"] = get_size(details.get("abs_file"))
        with open(show_file, "w") as out:
            json.dump(details, out)
    return parse_show_details(details, hour)
