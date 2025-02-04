#!/usr/bin/env python3

from django.urls import path, register_converter


from spidercheck import views
from spidercheck import converters


app_name = 'spidercheck'


register_converter(converters.SiteConverter, 'site')
register_converter(converters.PageConverter, 'page')


def tie(ruta, vista, name=None):
    return path(ruta, vista, name=name or vista.__name__)


urlpatterns = [
    tie('', views.homepage),
    tie('site/<site:site>/', views.site_detail),
    tie('site/<site:site>/errores/', views.site_errors),
    tie('site/<site:site>/queue/', views.site_queue),
    tie('site/<site:site>/scheduled/', views.site_scheduled),
    tie('site/<site:site>/last/', views.site_last),
    tie('site/<site:site>/no_links/', views.site_no_links),
    tie('site/<site:site>/search/', views.site_search),
    tie('site/<site:site>/orphans/', views.site_orphans),
    tie('site/<site:site>/expunge/', views.site_expunge),
    tie('site/<site:site>/expunge/all/', views.site_expunge_all),
    tie('page/<page:page>/', views.detail_page),
    tie('page/<page:page>/check/', views.page_check),
    tie('page/<page:page>/delete/', views.page_delete),
    tie('page/<page:page>/toogle/is_linkable/', views.toogle_is_linkable),
]
