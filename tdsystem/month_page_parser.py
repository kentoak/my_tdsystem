import datetime
import re
import urllib.request
from collections import namedtuple
from enum import Enum
from typing import Dict, List

from bs4 import BeautifulSoup
from bs4.element import Tag

from tdsystem.parser import Parser


class Course(Enum):
    SHORT = '25m'
    LONG = '50m'


class Meet:
    def __init__(self,
                 dates: List[datetime.date] = None,
                 name: str = None,
                 course: Course = None,
                 venue: str = None,
                 q_params: Dict[str, int] = None):
        self.dates = dates
        self.name = name
        self.course = course
        self.venue = venue
        self.q_params = q_params

    def addDate(self, date: datetime.date):
        if not self.dates:
            self.dates = []
        self.dates.append(date)

    def addQParam(self, key: str, val: int):
        if not self.q_params:
            self.q_params = {}
        self.q_params[key] = val

    def __str__(self):
        return 'name={}, dates={}, course={}, venue={}, q_params={}'.format(
            self.name, self.dates, self.course, self.venue, self.q_params)


class MonthPageParser(Parser):
    def __init__(self, page: Tag, year: int = 0, month: int = 0):
        self.year = year
        self.month = month
        self.page = page

    def getAvailableYears(self) -> List[str]:
        form = self.page.find('form', attrs={'name': 'SelectYear'})
        if not form:
            return None
        ys = []
        for yo in form.find_all('option', attrs={'name': 'SelYearList'}):
            ys.append(yo.get('value'))
        return ys

    SHORT_COURSE_PAT = re.compile(r'\((25m)\)')
    LONG_COURSE_PAT = re.compile(r'\((50m)\)')

    def getMeets(self) -> List[Meet]:
        form = self.page.find('form', attrs={'name': 'gamelist'})
        if not form:
            return None
        ms = []
        for tr in form.find_all('tr'):
            meet = Meet()
            tds = tr.find_all('td')
            if len(tds) < 4:
                continue
            meet.dates = self.getDays(self.normalize(tds[0].get_text()))
            meet.name = self.normalize(tds[1].get_text())

            # Process venue
            venue_text = self.normalize(tds[2].get_text())
            m = MonthPageParser.SHORT_COURSE_PAT.search(venue_text)
            if m:
                meet.course = Course(m.group(1))
                meet.venue = venue_text[0:m.span()[0]]
            m = MonthPageParser.LONG_COURSE_PAT.search(venue_text)
            if m:
                meet.course = Course(m.group(1))
                meet.venue = venue_text[0:m.span()[0]]

            b = tds[3].find('button')
            if b:
                meet.addQParam(b.get('name'), int(b.get('value')))

            ms.append(meet)
        return ms

    DATE_PAT = re.compile(r'([0-9]+)日\([日月火水木金土・祝]+\)')

    def getDays(self, days: str) -> List[datetime.datetime]:
        ret = []
        if not days:
            return None
        for m in MonthPageParser.DATE_PAT.finditer(days):
            ret.append(datetime.date(self.year, self.month, int(m.group(1))))
        return ret

    VenueInfo = namedtuple('VenueInfo', ('name', 'COURSE'))

    def processVenue(self, venue_text: str) -> VenueInfo:
        m = MonthPageParser.SHORT_COURSE_PAT.search(venue_text)
        if m:
            return self.VenueInfo(
                name=venue_text[0:m.span()[0]], course='short')

        m = MonthPageParser.LONG_COURSE_PAT.search(venue_text)
        if m:
            return MonthPageParser.VenueInfo(
                name=venue_text[0:m.span()[0]], course='long')

        return MonthPageParser.VenueInfo(name=venue_text)


if __name__ == '__main__':
    req = urllib.request.Request('{}?{}'.format(
        'http://www.tdsystem.co.jp/',
        urllib.parse.urlencode({
            'Y': '2018',
            'M': '08'
        })))
    with urllib.request.urlopen(req) as res:
        page = BeautifulSoup(res, 'lxml')
        p = MonthPageParser(2018, 8, page)
        ms = p.getMeets()
        for m in ms:
            print(m)
