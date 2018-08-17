import datetime
import re
from typing import List

from bs4.element import Tag

from tdsystem.parser import Parser


class TopPageParser(Parser):
    @staticmethod
    def getYears(form) -> List[str]:
        ret = []
        for yo in form.find_all('option', attrs={'name': 'SelYearList'}):
            ret.append(yo.get('value'))
        return ret

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
            meet['venue'] = TopPageParser.normalize(tds[2].get_text())

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
