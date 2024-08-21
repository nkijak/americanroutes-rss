import re
import logging
import time

from datetime import datetime
from dataclasses import dataclass
from zoneinfo import ZoneInfo
from typing import List, TypeVar, NewType
from requests_cache import CachedSession
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from tqdm import tqdm

from dateutil.parser import parse as date_parse


BASE = "https://amroutes.org"
OLD_GUID = "https://americanroutes.s3.amazonaws.com/shows/{show_id}.mp3"

T = TypeVar("T")
Html = NewType("Html", str)
Link = NewType("Link", str)

logging.basicConfig(level=logging.DEBUG)


def __flatten(matrix: List[List[T]]) -> List[T]:
    return [item for row in matrix for item in row]


# FIXME file length in bytes, reporting as zero even when in files
@dataclass
class Episode:
    title: str
    description: str
    date: datetime
    media_url: str
    url: str
    hour: int = 1
    media_size_bytes: int = 1

    def guid(self):
        show_id_hour = self.media_url.split("/")[-1][:-4]
        if self.date < datetime(
            year=2024,
            month=2,
            day=22,
            hour=0,
            minute=0,
            tzinfo=ZoneInfo("America/New_York"),
        ):
            return OLD_GUID.format(show_id=show_id_hour)
        else:
            return show_id_hour


def _parse_year(html: Html) -> List[Link]:
    """Parses the {BASE}/{year} page, and returns the URLs to each month's archive page"""
    soup = BeautifulSoup(html, "html.parser")
    month_links = [
        Link(f"{BASE}{mon.parent.get('href')}")
        for mon in soup.find_all("strong")
        if mon.parent.get("href")
    ]
    current_month = datetime.now().strftime("%B-%Y").lower()
    current_link_guess = Link(f"{BASE}/{current_month}") 
    if current_link_guess not in month_links:
        logging.info(f"didn't find {current_link_guess} in archives. Adding it")
        month_links.append(current_link_guess)
        month_links.append(Link(f"{current_link_guess}-1"))
    return month_links


def parse_month(html: Html) -> List[Link]:
    soup = BeautifulSoup(html, "html.parser")
    return [
        Link(f'{BASE}{details.find("a", "blog-more-link").get("href")}')
        for details in soup.find_all("div", "blog-item-text")
    ]


def parse_episodes(show_html: Html) -> List[Episode]:
    soup = BeautifulSoup(show_html, "html.parser")
    meta = {
        m.get("property", m.get("itemprop", m.get("name"))): m.get("content")
        for m in soup.find_all("meta")
    }
    media = [
        {
            "hour": i + 1,
            "media_url": div.get("data-url"),
            "date": date_parse(meta.get("datePublished")).replace(
                hour=i + 1,
                minute=0,
                second=0,
                microsecond=0,
                tzinfo=ZoneInfo("America/New_York"),
            ),
        }
        for i, div in enumerate(soup.find_all("div", "sqs-audio-embed"))
    ]
    params = {
        # drop the end, python style
        "title": meta.get("headline", "headline missing").replace("\xa0", " "),
        "description": re.sub(
            r"\s+",
            " ",
            meta.get("description", "description missing").replace("\n", ""),
        ),
        "url": meta.get("url"),
    }
    return [Episode(**{**m, **p}) for m, p in zip(media, [params, params])]


def _fetch_content(links: List[Link]) -> List[Html]:
    time.sleep(1)
    retry_strategy = Retry(total=4, status_forcelist=[429], backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = CachedSession("cachedir", backend="filesystem", cache_control=True)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    bodies = []
    for link in tqdm(links):
        response = session.get(
            link,
            headers={
                "User-Agent": "Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail Firefox/firefoxversion"
            },
        )
        if response.status_code // 100 == 2:
            bodies.append(Html(str(response.content, "utf-8")))
        else:
            logging.warning(f"failed to fetch {link}, got status {response.status_code}")
    return bodies


def pipeline(start_year: int = 2024) -> List[Episode]:
    years = range(start_year, datetime.now().year + 1)
    year_pages: List[Html] = _fetch_content([Link(f"{BASE}/{y}") for y in years])

    month_links: List[Link] = __flatten([_parse_year(page) for page in year_pages])
    month_pages: List[Html] = _fetch_content(month_links)

    show_links: List[Link] = __flatten([parse_month(page) for page in month_pages])
    show_pages: List[Html] = _fetch_content(show_links)

    return __flatten([parse_episodes(page) for page in show_pages])
