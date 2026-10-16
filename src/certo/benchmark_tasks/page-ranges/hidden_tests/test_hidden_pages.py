import pytest
from pages import format_pages, parse_pages


@pytest.mark.parametrize(
    "spec, last, expected",
    [
        ("1-3,5,7-9", 10, [1, 2, 3, 5, 7, 8, 9]),
        ("4", 4, [4]),
        ("3-3", 5, [3]),
        ("8-", 10, [8, 9, 10]),
        ("5-", 5, [5]),
        ("-3", 10, [1, 2, 3]),
        ("1-5,3-7", 10, [1, 2, 3, 4, 5, 6, 7]),
        (" 2 - 4 , 6 ", 6, [2, 3, 4, 6]),
        ("9,1,9", 9, [1, 9]),
        ("1-1", 1, [1]),
    ],
)
def test_parse(spec, last, expected):
    assert parse_pages(spec, last) == expected


@pytest.mark.parametrize(
    "spec, last",
    [
        ("", 10),
        ("  ", 10),
        ("1,,3", 10),
        ("a", 10),
        ("-", 10),
        ("1-2-3", 10),
        ("0", 10),
        ("11", 10),
        ("5-11", 10),
        ("4-2", 10),
        ("1", 0),
        ("2,", 10),
    ],
)
def test_parse_rejects(spec, last):
    with pytest.raises(ValueError):
        parse_pages(spec, last)


@pytest.mark.parametrize(
    "pages, expected",
    [
        ([9, 1, 2, 3, 5, 8, 7, 3], "1-3,5,7-9"),
        ([], ""),
        ([4], "4"),
        ([1, 2], "1-2"),
        ([1, 3, 5], "1,3,5"),
        ([10, 11, 12, 2], "2,10-12"),
    ],
)
def test_format(pages, expected):
    assert format_pages(pages) == expected


def test_round_trip():
    pages = [1, 2, 3, 6, 9, 10]
    assert parse_pages(format_pages(pages), 10) == pages
