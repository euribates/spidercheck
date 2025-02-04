#!/usr/bin/env python3

import re


PAT_VERSION = re.compile(r'<meta name="version" content="(\d+)">')


def process(_page, headers, body):
    '''Obtener el numero de versión.'''
    from spidercheck.core import content_is_html
    if content_is_html(headers):
        match = PAT_VERSION.search(body)
        if match:
            version = match.group(1)
            return {'version': version}
    return {}
