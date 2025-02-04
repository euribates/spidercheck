#!/usr/bin/env python3

from typing import Final


INDEX_NAME: Final = 'web'

INDEX_SCHEMA: Final = {
    'name': INDEX_NAME,
    'fields': [
        {'name': 'id', 'type': 'string'},
        {'name': 'page_id', 'type': 'int64'},
        {'name': 'url', 'type': 'string'},
        {'name': 'title', 'type': 'string'},
        {'name': 'keywords', 'type': 'string[]'},
        {'name': 'area', 'type': 'string', 'facet': True},
        {'name': 'h1', 'type': 'string[]'},
        {'name': 'h2', 'type': 'string[]'},
        {'name': 'h3', 'type': 'string[]'},
        {'name': 'h4', 'type': 'string[]'},
        {'name': 'h5', 'type': 'string[]'},
        {'name': 'h6', 'type': 'string[]'},
        {'name': 'body', 'type': 'string'},
        {'name': 'version', 'type': 'int32', 'facet': True},
    ],
    'default_sorting_field': 'page_id'
    }

SEARCH_FIELDS = [
    'url',
    'title',
    'keywords',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'body',
    ]


def search_web(query):
    fields = SEARCH_FIELDS
    filters = ''
    yield from _sa.search_documents(INDEX_NAME, query, fields, filters=filters)
