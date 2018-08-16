from tdsystem.crawler import TopPageParser


def test_getDays():
    assert TopPageParser.getDays('23日(月)') == ['23']
