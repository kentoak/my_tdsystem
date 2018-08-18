import datetime

from tdsystem.month_page_parser import MonthPageParser


def test_get_days_1day():
    p = MonthPageParser(year=2018, month=8, page=None)
    assert p.get_days('23日(月)') == [datetime.date(2018, 8, 23)]


def test_get_days_2days():
    p = MonthPageParser(year=2018, month=8, page=None)
    assert p.get_days('25日(土)～26日(日)') == [
        datetime.date(2018, 8, 25),
        datetime.date(2018, 8, 26)
    ]
