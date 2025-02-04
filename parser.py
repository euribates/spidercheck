#!/usr/bin/env python3

import re
import itertools
from typing import Final

from html.parser import HTMLParser

EXCLUDE_PATHS: Final = [
    re.compile(r'/api/', re.IGNORECASE),
    re.compile(r'/api2/', re.IGNORECASE),
    re.compile(r'/__debug__/', re.IGNORECASE),
    ]


def is_valid_url(url: str) -> bool:
    for _pattern in EXCLUDE_PATHS:
        if _pattern.match(url):
            return False
    return True


class LinkExtractor(HTMLParser):

    def __init__(self, *args, **kwargs):
        super(LinkExtractor, self).__init__(*args, **kwargs)
        self.links = set()
        self.images = set()
        self.styles = set()
        self.scripts = set()

    def all_links(self):
        return itertools.chain(
            self.styles,
            self.scripts,
            self.images,
            self.links,
        )

    def handle_starttag(self, tag, attrs):
        parameters = dict(attrs)
        if tag == 'a':
            if url := parameters.get('href'):
                if is_valid_url(url):
                    self.links.add(url)
        elif tag == 'link':
            if url := parameters.get('href'):
                self.styles.add(url)
        elif tag == 'img':
            if url := parameters.get('src'):
                self.images.add(url)
        elif tag == 'script':
            if url := parameters.get('src'):
                self.scripts.add(url)
