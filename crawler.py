import pickle
import time
import urllib.request
from logging import INFO, Formatter, StreamHandler, getLogger
from typing import Dict, List
from bs4 import BeautifulSoup
import re
from meet_page_parser import MeetPageParser, Race
from month_page_parser import Meet, MonthPageParser
from record_page_parser import Record, RecordPageParser

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
    def __fetch(url):
        if Crawler.prev:
            past = time.time() - Crawler.prev
            wait = 0 if past > Crawler.INTERVAL_SEC else Crawler.INTERVAL_SEC
            time.sleep(wait)
        Crawler.prev = time.time()
        if type(url) is str:
            logger.info(url)
        else:
            logger.info(url.get_full_url())
        #print("url is ......",url)
        return urllib.request.urlopen(url)

    @staticmethod
    def fetch_years(url: str) -> List[str]:
        with Crawler.__fetch(url) as res:
            p = MonthPageParser(BeautifulSoup(res, 'lxml'))
            years = p.get_available_years()
            return years

    @staticmethod
    def fetch_meets(baseurl: str, year: str, month: str) -> List[Meet]:
        req = urllib.request.Request('{}?{}'.format(
            baseurl, urllib.parse.urlencode({
                'Y': year,
                'M': month
            })))
        with Crawler.__fetch(req) as res:
            p = MonthPageParser(
                page=BeautifulSoup(res, 'lxml'),
                year=int(year),
                month=int(month))
            return p.get_meets()

    @staticmethod
    def fetch_races(baseurl: str, q_params: Dict[str, str]) -> List[Race]:
        req = urllib.request.Request('{}?{}'.format(
            baseurl + q_params.pop('action'),
            urllib.parse.urlencode(q_params)))
        with Crawler.__fetch(req) as res:
            p = MeetPageParser(BeautifulSoup(res, 'lxml'))
            return p.get_races()

    @staticmethod
    def fetch_records(baseurl: str, q_params: Dict[str, str]) -> List[Record]:
        url = baseurl + q_params.pop('action')
        # print("url is/////",url)
        # print("q_params",q_params)
        # print("urllib.parse.urlencode(q_params)",urllib.parse.urlencode(q_params))
        req = urllib.request.Request('{}?{}'.format(
            url, urllib.parse.urlencode(q_params)))
        with Crawler.__fetch(req) as res:
            p = RecordPageParser(BeautifulSoup(res, 'lxml'))
            params = p.get_query_params()
            classes = p.get_available_classes()
        if not params:
            params = q_params
        if not classes:
            classes = {'999': 'DUMMY'}  # Put the wildcard class

        rs = []
        for cls in classes.keys():
            params['Cls'] = cls
            req = urllib.request.Request('{}?{}'.format(
                url, urllib.parse.urlencode(params)))
            with urllib.request.urlopen(req) as res:
                p = RecordPageParser(
                    BeautifulSoup(res, 'lxml'), params, classes[cls])
                rs.extend(p.get_records())
        return rs


def crawl_all(base_url: str): #https://www.tdsystem.co.jp/のとき、全ての年をパース
    years = Crawler.fetch_years(baseurl)
    for y in years:
        for m in range(1, 12):
            meets = Crawler.fetch_meets(baseurl, y, m)
            for meet in meets:
                for r in Crawler.fetch_races(baseurl, meet.q_params):
                    Crawler.fetch_records(baseurl, r.q_params)
                    # TODO Store somewhere


def crawl_records(base_url: str, record_page_params: Dict[str, str]) -> List[Record]:
    return Crawler.fetch_records(baseurl, record_page_params)


if __name__ == '__main__':
    string=input("tdsystemのRecord.phpのlinkを入力してください: ")
    baseurl = 'https://www.tdsystem.co.jp/'
    y_pattern = r"Y=(\d+)"
    m_pattern = r"M=(\d+)"
    g_pattern = r"&G=(\d+)"
    gl_pattern = r"GL=(\d+)"
    s_pattern = r"S=(\d+)"
    lap_pattern = r"Lap=(\d+)"
    cls_pattern = r"Cls=(\d+)"
    l_pattern = r"&L=(\d+)"
    p_pattern = r"P=(\d+)"
    #p_pattern = r"Page=(\w+\.php)"

    y_match = re.search(y_pattern, string)
    m_match = re.search(m_pattern, string)
    #g_match = re.search(g_pattern, string) #e.g.)  https://www.tdsystem.co.jp/ProList.php?Y=2023&M=2&G=0&GL=0&G=48 など、G=が2つあるので。
    g_matches = re.findall(g_pattern, string)
    gl_match = re.search(gl_pattern, string)
    s_match = re.search(s_pattern, string)
    lap_match = re.search(lap_pattern, string)
    cls_match = re.search(cls_pattern, string)
    l_match = re.search(l_pattern, string)
    p_matches = re.findall(p_pattern, string)
    #p_match = re.search(p_pattern, string)

    if y_match:
        y_value = y_match.group(1)
        print("Y value:", y_value)

    if m_match:
        m_value = m_match.group(1)
        print("M value:", m_value)

    # if g_match:
    #     g_value = g_match.group(1)
    #     print("G value:", g_value)
    if g_matches:
        g_value = g_matches[-1]
        print("G value:", g_value)

    if gl_match:
        gl_value = gl_match.group(1)
        print("GL value:", gl_value)

    if s_match:
        s_value = s_match.group(1)
        print("S value:", s_value)
    else:
        s_value="2"

    if lap_match:
        lap_value = lap_match.group(1)
        print("Lap value:", lap_value)
    else:
        lap_value="1"

    if cls_match:
        cls_value = cls_match.group(1)
        print("Cls value:", cls_value)
    else:
        cls_value="999"

    if l_match:
        l_value = l_match.group(1)
        print("L value:", l_value)
    else:
        l_value="1"

    if p_matches:
        p_value = p_matches[-1]
        print("P value:", p_value)
    else:
        p_value="1"

    # if p_match:
    #     p_value = p_match.group(1)
    #     #print("P value:", p_value)
    # else:
    #     p_value="ProList.php"

    rs = crawl_records(
        baseurl, {
            'action': 'Record.php',
            'Y': y_value,
            'M': m_value,
            'GL': gl_value,
            'G': g_value,
            'S': s_value,
            'Lap': lap_value,
            'Cls': cls_value,
            'L': l_value,
            'P': p_value
        })
    #print(rs)
    with open('records.pickle', 'wb') as f:
        pickle.dump(rs, f, pickle.HIGHEST_PROTOCOL)

    with open('records.pickle', 'rb') as f:
        rs = pickle.load(f)
        for r in rs:
            print(r)
