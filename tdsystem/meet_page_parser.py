import re
import urllib.request
from enum import Enum
from typing import List

from bs4 import BeautifulSoup
from bs4.element import Tag

from tdsystem.parser import Parser


class Sex(Enum):
    M = '男子'
    F = '女子'
    X = '混合'


class Style(Enum):
    FR = '自由形'
    BR = '平泳ぎ'
    BA = '背泳ぎ'
    FLY = 'バタフライ'
    IM = '個人メドレー'
    FRR = 'フリーリレー'
    MR = 'メドレーリレー'


class Race:
    def __init__(self, sex: Sex = None, distance: int = 0,
                 style: Style = None):
        self.sex = sex
        self.distance = distance
        self.style = style

    def __str__(self):
        return 'sex={}, distance={}, style={}'.format(self.sex, self.distance,
                                                      self.style)


class MeetPageParser(Parser):
    def __init__(self, page: Tag):
        self.page = page

    SEX_PAT = re.compile(r'女子|男子|混合')
    INDV_DIST_PAT = re.compile(r'([0-9]+)m')
    RELAY_DIST_PAT = re.compile(r'4×([0-9]+)m')
    STYLE_PAT = re.compile(r'自由形|背泳ぎ|平泳ぎ|バタフライ|個人メドレー|フリーリレー|メドレーリレー')

    def getRaces(self) -> List[Race]:
        rs = []
        form = self.page.find('form', attrs={'name': 'gamelist'})
        for tr in form.find_all('tr'):
            r = Race()
            for td in tr.find_all('td'):
                txt = self.normalize(td.get_text())
                if not txt:
                    continue
                m = self.SEX_PAT.match(txt)
                if m:
                    r.sex = Sex(m.group(0))
                    continue
                m = self.INDV_DIST_PAT.match(txt)
                if m:
                    r.distance = int(m.group(1))
                m = self.RELAY_DIST_PAT.match(txt)
                if m:
                    r.distance = int(m.group(1)) * 4
                m = self.STYLE_PAT.match(txt)
                if m:
                    r.style = Style(m.group(0))
            rs.append(r)
        return rs


if __name__ == '__main__':
    with urllib.request.urlopen(
            'http://www.tdsystem.co.jp/ProList.php?Y=2018&M=6&GL=0&G=154'
    ) as res:
        soup = BeautifulSoup(res, 'lxml')
        p = MeetPageParser(soup)
        rs = p.getRaces()
        for r in rs:
            print(r)
