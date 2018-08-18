import time
import urllib.request
from logging import INFO, Formatter, StreamHandler, getLogger
from typing import List

from bs4 import BeautifulSoup

from tdsystem.month_page_parser import Meet, MonthPageParser

logger = getLogger(__name__)
handler = StreamHandler()
handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s'))
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)


class Crawler:
    prev = None
    INTERVAL_SEC = 5

    @staticmethod
    def fetch(url):
        if Crawler.prev:
            past = time.time() - Crawler.prev
            wait = 0 if past > Crawler.INTERVAL_SEC else Crawler.INTERVAL_SEC
            time.sleep(wait)
        Crawler.prev = time.time()
        if type(url) is str:
            logger.info(url)
        else:
            logger.info(url.get_full_url())
        return urllib.request.urlopen(url)

    @staticmethod
    def fetchYears(url: str) -> List[str]:
        with Crawler.fetch(url) as res:
            p = MonthPageParser(BeautifulSoup(res, 'lxml'))
            years = p.getAvailableYears()
            return years

    @staticmethod
    def fetchMeets(baseurl: str, year: str, month: str) -> List[Meet]:
        req = urllib.request.Request('{}?{}'.format(
            baseurl, urllib.parse.urlencode({
                'Y': year,
                'M': month
            })))
        with Crawler.fetch(req) as res:
            p = MonthPageParser(
                page=BeautifulSoup(res, 'lxml'),
                year=int(year),
                month=int(month))
            return p.getMeets()


if __name__ == '__main__':
    baseurl = 'http://www.tdsystem.co.jp/'
    years = Crawler.fetchYears(baseurl)
    for y in years:
        if y == '2019':  # TODO: Tentative code
            continue
        for m in range(1, 12):
            meets = Crawler.fetchMeets(baseurl, y, m)
            for meet in meets:
                print(meet)
