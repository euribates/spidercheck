#!/usr/bin/env python3

from spidercheck.models import Site
from spidercheck.models import Page


class SiteConverter:
    regex = r'[-\w]+'

    def to_python(self, value):
        if isinstance(value, Site):
            return value
        site = Site.load_site_by_name(value)
        if site is None:
            raise ValueError(
                "El identificador del site especificado es incorrecto"
                )
        return site

    def to_url(self, value):
        if isinstance(value, str):
            return value
        if isinstance(value, Site):
            return value.name
        raise ValueError(
            "Se necesita una instancia de la clase Site, o"
            " una cadena de texto con el nobre del site."
            )


class PageConverter:
    regex = r'\d+'

    def to_python(self, value):
        if isinstance(value, Page):
            return value
        page = Page.load_page(value)
        if page is None:
            raise ValueError(
                "El identificador de la página especificada"
                " es incorrecto"
                )
        return page

    def to_url(self, value):
        if isinstance(value, int):
            return value
        if isinstance(value, Page):
            return value.pk
        raise ValueError(
            "Se necesita una instancia de la clase Page, o"
            " un número entero con la clave prinaria de"
            " la página."
            )
