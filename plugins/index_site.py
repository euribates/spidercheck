#!/usr/bin/env python3

from io import StringIO
from html.parser import HTMLParser

from bs4 import BeautifulSoup

from adapters.search import search_adapter as _sa
from spidercheck.search import INDEX_NAME


class MLStripper(HTMLParser):

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, data):
        self.text.write(data)

    def get_data(self):
        only_text = self.text.getvalue()
        return ' '.join(only_text.split())


def strip_tags(html):
    stripper = MLStripper()
    stripper.feed(html)
    return stripper.get_data()


def _get_info(page, _headers, body):
    soup = BeautifulSoup(body, 'html.parser')
    title = soup.find('title').text
    keywords = []
    area = ''
    version = 0
    for _meta in soup.find_all('meta'):
        name = _meta.attrs.get('name', '')
        if name == 'area':
            area = _meta.attrs.get('content', '')
        elif name == 'version':
            value = _meta.attrs.get('content', '')
            if value.isdigit():
                version = int(value)
        elif name == 'keywords':
            value = _meta.attrs.get('content', '')
            if value:
                keywords = [_.strip().lower() for _ in value.split(',')]
    main = soup.find('main')
    if not main:
        main = soup.find('body')
    body = strip_tags(main.text)
    url = str(page.get_relative_url())
    result = {
        'id': url,
        'page_id': page.pk,
        'url': url,
        'title': title,
        'keywords': keywords,
        'area': area,
        'h1': [_.text.strip() for _ in main.find_all('h1')],
        'h2': [_.text.strip() for _ in main.find_all('h2')],
        'h3': [_.text.strip() for _ in main.find_all('h3')],
        'h4': [_.text.strip() for _ in main.find_all('h4')],
        'h5': [_.text.strip() for _ in main.find_all('h5')],
        'h6': [_.text.strip() for _ in main.find_all('h6')],
        'body': body,
        'version': version,
    }
    return result


def process(page, headers, body):
    '''Indexar la pagina.
    '''
    from spidercheck.core import content_is_html
    if content_is_html(headers):
        data = _get_info(page, headers, body)
        _sa.add_documents(INDEX_NAME, [data])
    return {}
