#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

pat_html_begin = re.compile('<html.*>', re.IGNORECASE)


def is_valid_html(body):
    body = body.strip()
    if len(body) < 14:
        return False
    if body[-7:].lower() != '</html>':
        return False
    if not pat_html_begin.search(body):
        return False
    return True
