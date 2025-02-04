#!/usr/bin/env python3


from django.urls import reverse_lazy


def a_homepage():
    return reverse_lazy('intranet:spidercheck:homepage')


def a_detalle_pagina(page_or_pk):
    return reverse_lazy('intranet:spidercheck:detail_page', kwargs={
        'page': page_or_pk,
        })


def a_detalle_site(site_or_name):
    return reverse_lazy('intranet:spidercheck:site_detail', kwargs={
        'site': site_or_name,
        })


def a_site_errors(site_or_name):
    return reverse_lazy('intranet:spidercheck:site_errors', kwargs={
        'site': site_or_name,
        })


def a_site_no_links(site_or_name):
    return reverse_lazy('intranet:spidercheck:site_no_links', kwargs={
        'site': site_or_name,
        })


def a_site_orphans(site_or_name):
    return reverse_lazy('intranet:spidercheck:site_orphans', kwargs={
        'site': site_or_name,
        })


def a_site_last(site_or_name):
    return reverse_lazy('intranet:spidercheck:site_last', kwargs={
        'site': site_or_name,
        })


def a_site_scheduled(site_or_name):
    return reverse_lazy('intranet:spidercheck:site_scheduled', kwargs={
        'site': site_or_name,
        })


def a_site_queue(site_or_name):
    return reverse_lazy('intranet:spidercheck:site_queue', kwargs={
        'site': site_or_name,
        })


def a_add_no_link(site_or_name):
    return reverse_lazy('intranet:spidercheck:add_no_link', kwargs={
        'site': site_or_name,
        })
