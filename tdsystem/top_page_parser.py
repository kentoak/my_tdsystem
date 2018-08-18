import datetime
import re
import urllib.request
from collections import namedtuple
from typing import List

from bs4 import BeautifulSoup
from bs4.element import Tag

from tdsystem.parser import Parser


class TopPageParser(Parser):
    @staticmethod
    def getYears(form) -> List[str]:
        ret = []
        for yo in form.find_all('option', attrs={'name': 'SelYearList'}):
            ret.append(yo.get('value'))
        return ret

    SHORT_COURCE_PAT = re.compile(r'\(25m\)')
    LONG_COURCE_PAT = re.compile(r'\(50m\)')

    @staticmethod
    def getMeets(year: str, month: str, form: Tag):
        for tr in form.find_all('tr'):
            meet = {}
            tds = tr.find_all('td')
            if len(tds) < 4:
                continue
            meet['dates'] = TopPageParser.getDays(
                int(year), int(month),
                TopPageParser.normalize(tds[0].get_text()))
            meet['name'] = TopPageParser.normalize(tds[1].get_text())

            # Process venue
            venue_text = TopPageParser.normalize(tds[2].get_text())
            m = TopPageParser.SHORT_COURCE_PAT.search(venue_text)
            if m:
                meet['course'] = 'short'
                meet['venue'] = venue_text[0:m.span()[0]]
            m = TopPageParser.LONG_COURCE_PAT.search(venue_text)
            if m:
                meet['course'] = 'long'
                meet['venue'] = venue_text[0:m.span()[0]]

            b = tds[3].find('button')
            if b:
                meet['g_id'] = b.get('value')

            print(meet)

    DATE_PAT = re.compile(r'([0-9]+)日\([日月火水木金土・祝]+\)')

    @staticmethod
    def getDays(year: int, month: int, days: str) -> List[datetime.datetime]:
        ret = []
        if not days:
            return None
        for m in TopPageParser.DATE_PAT.finditer(days):
            ret.append(datetime.date(year, month, int(m.group(1))))
        return ret

    VenueInfo = namedtuple('VenueInfo', ('name', 'cource'))

    @staticmethod
    def processVenue(venue_text: str) -> VenueInfo:
        m = TopPageParser.SHORT_COURCE_PAT.search(venue_text)
        if m:
            return TopPageParser.VenueInfo(
                name=venue_text[0:m.span()[0]], course='short')

        m = TopPageParser.LONG_COURCE_PAT.search(venue_text)
        if m:
            return TopPageParser.VenueInfo(
                name=venue_text[0:m.span()[0]], course='long')

        return TopPageParser.VenueInfo(name=venue_text)


if __name__ == '__main__':
    req = urllib.request.Request('{}?{}'.format(
        'http://www.tdsystem.co.jp/',
        urllib.parse.urlencode({
            'Y': '2018',
            'M': '08'
        })))
    with urllib.request.urlopen(req) as res:
        soup = BeautifulSoup(res, 'lxml')
        TopPageParser.getMeets('2018', '08',
                               soup.find('form', attrs={'name': 'gamelist'}))
