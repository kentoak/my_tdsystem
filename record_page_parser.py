import re
import urllib.request
from datetime import timedelta
from enum import Enum
from typing import Dict, List

from bs4 import BeautifulSoup
from bs4.element import Tag

from parser_base import Parser


class Record:
    def __init__(self,
                 age_cls: str = None,
                 rank: int = 0,
                 name: str = None,
                 record: timedelta = None,
                 lap: List[timedelta] = None,
                 q_params: Dict[str, str] = None):
        self.age_cls = age_cls
        self.rank = rank
        self.record = record
        self.lap = lap
        self.name = name
        self.q_params = q_params

    def __str__(self):
        ret = 'age_cls={}, rank={}, name={}, record={}, lap=['.format(
            self.age_cls, self.rank, self.name, str(self.record))
        l_txt = ''
        if self.lap:
            print("self.lap",self.lap)
            for l in self.lap:
                if len(l_txt) > 0:
                    l_txt += ', '
                l_txt += str(l)
        ret += l_txt
        ret += '], '
        ret += 'q_params={}'.format(self.q_params)
        return ret

    def set_record(self, mins: int = 0, secs: int = 0,
                   one_tenth_secs: int = 0):
        self.record = timedelta(
            minutes=mins, seconds=secs, milliseconds=one_tenth_secs * 10)

    def add_lap(self, mins: int = 0, secs: int = 0, one_tenth_secs: int = 0):
        if not self.lap:
            self.lap = []
        self.lap.append(
            timedelta(
                minutes=mins, seconds=secs, milliseconds=one_tenth_secs * 10))
    
    def set_name(self, name:""):
        self.name= name


class RecordPageParser(Parser):
    def __init__(self,
                 page: Tag,
                 q_params: Dict[str, str] = None,
                 age_cls: str = None):
        self.page = page
        self.q_params = q_params
        self.age_cls = age_cls

    def get_query_params(self) -> Dict[str, str]:
        form = self.page.find('form', attrs={'name': 'formclasslist'})
        if not form:
            return None
        params = {}
        for input in form.find_all('input', attrs={'type': 'hidden'}):
            params[input.get('name')] = input.get('value')
        return params

    def get_available_classes(self) -> Dict[str, str]:
        form = self.page.find('form', attrs={'name': 'formclasslist'})
        if not form:
            return None
        select = form.find('select')
        if not select:
            return None
        classes = {}
        for c in select.find_all('option'):
            value = c.get('value')
            if value == '999':  # Wildcard
                continue
            classes[value] = self.normalize(c.get_text())
        return classes

    def get_records(self) -> List[Record]:
        for t in self.page.find_all('table'):
            if not self.has_records(t):
                continue
            return self.__get_records(t)
        return None

    def has_records(self, table: Tag) -> bool:
        th = table.find('th')
        if th and th.get_text() == '順位':
            return True
        return False

    RECORD_PAT = re.compile(r'([0-9]{0,2}):{0,1}([0-9]{2}).([0-9]{2})')

    RowType = Enum('RowType', ('RECORD', 'LAP'))

    def __init_record(self):
        return Record(q_params=self.q_params.copy(), age_cls=self.age_cls)

    def __get_records(self, table: Tag) -> List[Record]:
        rs = []
        r = self.__init_record()
        isLap = False
        for idx,tr in enumerate(table.find_all('tr', recursive=False)): ##//written by taoka on 2023/02/20 
            if idx==3: #lapありなしを判定
                break
            rt = self.__get_row_type(tr)
            if not rt:
                continue
            #print("idx",idx,"rt is ,,,,",rt,tr)
            if rt == self.__class__.RowType.LAP:
                isLap = True

        for tr in table.find_all('tr', recursive=False):
            #print(tr)
            rt = self.__get_row_type(tr)
            if not rt:
                continue
            #print("rt is ,,,,",rt,tr)
            if rt == self.__class__.RowType.RECORD:
                #print(tr)
                name=""
                for i, td in enumerate(tr.find_all('td')):
                    txt = self.normalize(td.get_text())
                    if not txt:
                        continue
                    #print("txt is ...",txt)
                    #print("td is ...",td)
                    if '<td valign="top">' in str(td) and not name:
                        name=td.text
                        #print("name",name)
                    r.set_name(name)
                    if i == 0:
                        r.rank = int(txt)
                    m = self.__class__.RECORD_PAT.match(txt)
                    #print("m is ...",m)
                    if not m:
                        continue
                    #print("m is ...",m)
                    # if len(m.group(1)) > 0:
                    #     print("m.group(1)",m.group(1))
                    # print("m.group(2)",m.group(2))
                    # print("m.group(3)",m.group(3))
                    r.set_record(
                        mins=int(m.group(1)) if len(m.group(1)) > 0 else 0,
                        secs=int(m.group(2)),
                        one_tenth_secs=int(m.group(3))) #r.recordを作る
                    #if td.get('valign'):
                    #print("r.record is ...\n",r.record)
            elif rt == self.__class__.RowType.LAP:
                rt = tr.find('table')
                if not rt:
                    continue
                for td in rt.find_all('td'):
                    txt = self.normalize(td.get_text())
                    if not txt:
                        continue
                    m = self.__class__.RECORD_PAT.match(txt)
                    if not m:
                        continue
                    r.add_lap(
                        mins=int(m.group(1)) if len(m.group(1)) > 0 else 0,
                        secs=int(m.group(2)),
                        one_tenth_secs=int(m.group(3)))
                    #print("r.lap is ...\n",r.lap)
            # Store the previous record before processing this new record
            if isLap:
                if r.lap:
                    rs.append(r)
                    r = self.__init_record()
                #print(r.record)
            else:
                if r.record:
                    rs.append(r)
                    r = self.__init_record()
        #print("rs is ...",rs)
        return rs

    def __get_row_type(self, tr: Tag) -> RowType:
        td = tr.find('td')  # Get 1st td
        #print(" Get 1st td",td)
        if not td:
            return None
        txt = self.normalize(td.get_text())
        #print(" Get 1st td_txt",txt)
        pattern = r'^\d+$'  # 数字以外の文字を含まない文字列にマッチする正規表現パターン
        #if txt and re.match('[0-9]+', txt):
        if txt and re.match(pattern, txt):
            return self.__class__.RowType.RECORD
        else:
            return self.__class__.RowType.LAP


if __name__ == '__main__':
    ex_url='http://www.tdsystem.co.jp/Record.php?' + 'Y=2018&M=6&G=154&GL=0&L=1&Page=ProList.php&P=10&S=2&Lap=1&Cls=50'
    print("ex_url is ",ex_url)
    with urllib.request.urlopen(ex_url) as res:
        p = RecordPageParser(BeautifulSoup(res, 'lxml'))
        params = p.get_query_params()
        classes = p.get_available_classes()
    #print(params) #{'Y': '2018', 'M': '6', 'G': '154', 'GL': '0', 'S': '2', 'Lap': '1', 'Cls': '50', 'L': '1', 'RG': '1', 'Page': 'ProList.php', 'P': '10'}
    #print(classes.keys()) #e.g.)dict_keys(['80', '75', '70', '65', '60', '55', '50', '45', '40', '35', '30', '25'])
    for idx,cls in enumerate(classes.keys()):
        # if idx==1:
        #     break
        params['Cls'] = cls
        req = urllib.request.Request('{}?{}'.format(
            'http://www.tdsystem.co.jp/Record.php',
            urllib.parse.urlencode(params)))
        #sprint("req.get_full_url():",req.get_full_url())
        with urllib.request.urlopen(req) as res:
            p = RecordPageParser(BeautifulSoup(res, 'lxml'), params, classes[cls])
            rs = p.get_records()
            for r in rs:
                #print("r is ...",r)
                print(r,"\n")
