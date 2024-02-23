from typing import List
from pathlib import Path
from datetime import datetime

import requests
from dateutil.rrule import rrule, MONTHLY
from tqdm import tqdm


# import boto3

from feedgen.feed import FeedGenerator
from crawler.parser import Episode, parse_archives

BUCKETNAME = "americanroutes"


def episodeToFeedEntry(episode: Episode, entry):
    entry.id(episode.media_url)
    entry.enclosure(episode.media_url, 0, "audio/mp3")
    entry.title(f"{episode.title} -- Hour {episode.hour}")
    entry.link(href=episode.url)
    entry.published(episode.date)
    entry.description(episode.description)


def generate(episodes: List[Episode]):
    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title("American Routes by PRX")
    fg.podcast.itunes_image(
        "http://americanroutes.wwno.org/images/AR-Logo-1-1569270059.png"
    )
    fg.image("http://americanroutes.wwno.org/images/AR-Logo-1-1569270059.png")
    fg.description(
        """American Routes is a weekly two-hour public radio program produced in New Orleans, presenting a broad range of American music — blues and jazz, gospel and soul, old-time country and rockabilly, Cajun and zydeco, Tejano and Latin, roots rock and pop, avant-garde and classical. Now in our 20th year on the air, American Routes explores the shared musical and cultural threads in these American styles and genres of music — and how they are distinguished.

The program also presents documentary features and artist interviews. Our conversations include Willie Nelson, Tom Waits, B.B. King, Dr. John, Dave Brubeck, Elvis Costello, Ray Charles, Randy Newman, McCoy Tyner, Lucinda Williams, Rufus Thomas, Jerry Lee Lewis and many others. Join us as we ride legendary trains, or visit street parades, instrument-makers, roadside attractions and juke joints, and meet tap dancers, fishermen, fortunetellers and more.

The songs and stories on American Routes describe both the community origins of our music, musicians and cultures (the “roots”) and the many directions they take over time."""
    )
    fg.author({"name": "Nick Spitzer", "email": "mail@amroutes.org"})
    fg.podcast.itunes_author("Nick Spitzer")
    fg.link(href="http://americanroutes.wwno.org", rel="alternate")
    fg.language("en")
    for ep in episodes:
        episodeToFeedEntry(ep, fg.add_entry())
    fg.rss_file("target/rss.xml")


if __name__ == "__main__":
    months = [
        dt for dt in rrule(MONTHLY, dtstart=datetime(2023, 11, 1), until=datetime.now())
    ]

    urls = [
        f"http://americanroutes.wwno.org/archives/for_date/{m.strftime('%Y-%m')}"
        for m in months
    ]
    episodes: List[Episode] = []
    for url in tqdm(urls, desc="Archives"):
        html = str(requests.get(url).content, "utf-8")
        episodes += reversed(parse_archives(html, Path("target")))
    generate(episodes)
