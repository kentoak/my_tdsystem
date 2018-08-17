from tdsystem.crawler import TopPageParser


def test_getDays_1day():
    assert TopPageParser.getDays('23日(月)') == ['23']


def test_getDays_2days():
    assert TopPageParser.getDays('25日(土)～26日(日)') == ['25', '26']
