import re
import urllib.request
from datetime import timedelta
from enum import Enum
from typing import List

from bs4 import BeautifulSoup
from bs4.element import Tag

from tdsystem.parser import Parser


class Record:
    def __init__(self,
                 rank: int = 0,
                 record: timedelta = None,
                 lap: List[timedelta] = None):
        self.rank = rank
        self.record = record
        self.lap = lap

    def __str__(self):
        ret = 'rank={}, record={}, lap=['.format(self.rank, str(self.record))
        l_txt = ''
        for l in self.lap:
            if len(l_txt) > 0:
                l_txt += ', '
            l_txt += str(l)
        ret += l_txt
        ret += ']'
        return ret

    def setRecord(self, mins: int = 0, secs: int = 0, one_tenth_secs: int = 0):
        self.record = timedelta(
            minutes=mins, seconds=secs, milliseconds=one_tenth_secs * 10)

    def addLap(self, mins: int = 0, secs: int = 0, one_tenth_secs: int = 0):
        if not self.lap:
            self.lap = []
        self.lap.append(timedelta(
            minutes=mins, seconds=secs, milliseconds=one_tenth_secs * 10))


class RecordPageParser(Parser):
    def __init__(self, page: Tag):
        self.page = page

    def getRecords(self) -> List[Record]:
        for t in self.page.find_all('table'):
            if not self.hasRecords(t):
                continue
            return self.__getRecords(t)
        return None

    def hasRecords(self, table: Tag) -> bool:
        th = table.find('th')
        if th and th.get_text() == '順位':
            return True
        return False

    RECORD_PAT = re.compile(r'([0-9]*):*([0-9]+).([0-9]+)')

    RowType = Enum('RowType', ('RECORD', 'LAP'))

    def __getRecords(self, table: Tag) -> List[Record]:
        rs = []
        r = Record()
        for tr in table.find_all('tr', recursive=False):
            rt = self.__getRowType(tr)
            if not rt:
                continue

            if rt == RecordPageParser.RowType.RECORD:
                for td in tr.find_all('td'):
                    txt = Parser.normalize(td.get_text())
                    if not txt:
                        continue
                    m = RecordPageParser.RECORD_PAT.match(txt)
                    if not m:
                        continue
                    r.setRecord(
                        mins=int(m.group(1)),
                        secs=int(m.group(2)),
                        one_tenth_secs=int(m.group(3)))
            elif rt == RecordPageParser.RowType.LAP:
                rt = tr.find('table')
                if not rt:
                    continue
                for td in rt.find_all('td'):
                    txt = Parser.normalize(td.get_text())
                    if not txt:
                        continue
                    m = RecordPageParser.RECORD_PAT.match(txt)
                    if not m:
                        continue
                    r.addLap(
                        mins=int(m.group(1)),
                        secs=int(m.group(2)),
                        one_tenth_secs=int(m.group(3)))
                rs.append(r)
                r = Record()
        return rs

    def __getRowType(self, tr: Tag) -> RowType:
        td = tr.find('td')  # Get 1st td
        if not td:
            return None

        txt = Parser.normalize(td.get_text())
        if txt and re.match('[0-9]+', txt):
            return RecordPageParser.RowType.RECORD
        else:
            return RecordPageParser.RowType.LAP


if __name__ == '__main__':
    with urllib.request.urlopen(
            'http://www.tdsystem.co.jp/Record.php?' +
            'Y=2018&M=6&G=154&GL=0&L=1&Page=ProList.php&P=10&S=2&Lap=1&Cls=50'
    ) as res:
        soup = BeautifulSoup(res, 'lxml')
        p = RecordPageParser(soup)
        rs = p.getRecords()
        for r in rs:
            print(r)
