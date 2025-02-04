#!/usr/bin/env python3

import pytest
from spidercheck import parser


SAMPLES = [
    ('/transparencia/', True),
    ('/apista', True),
    ('/api2ta', True),
    ('/api/transparencia/', False),
    ('/api2/transparencia/', False),
    ('/api2/sicres/', False),
    ('/api2/sicres/documento/3/1914/3936/1/pop-aplicacion-fondos-del-sce-1222', False),
]


@pytest.fixture(params=SAMPLES, ids=lambda _: _[0])
def urls(request):
    return request.param


def test_is_valid_url(urls):
    url, expected = urls
    assert parser.is_valid_url(url) is expected


if __name__ == "__main__":
    pytest.main()
