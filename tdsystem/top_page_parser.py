import re

from typing import List


class TopPageParser:
    @staticmethod
    def getYears(form) -> List[str]:
        ret = []
        for yo in form.find_all('option', attrs={'name': 'SelYearList'}):
            ret.append(yo.get('value'))
        return ret

    @staticmethod
    def getMeets(form):
        for tr in form.find_all('tr'):
            meet = {}
            tds = tr.find_all('td')
            if len(tds) < 4:
                continue
            meet['days'] = TopPageParser.getDays(tds[0].get_text())
            meet['name'] = tds[1].get_text()
            meet['venue'] = tds[2].get_text()
            b = tds[3].find('button')
            if b:
                meet['g'] = b.get('value')
            print(meet)

    DATE_PAT = re.compile(r'([0-9]+)日\([日月火水木金土・祝]+\)')

    @staticmethod
    def getDays(days: str) -> List[str]:
        ret = []
        if not days:
            return None
        for m in TopPageParser.DATE_PAT.finditer(days):
            ret.append(m.group(1))
        return ret
