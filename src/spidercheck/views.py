#!/usr/bin/env python3

from django.shortcuts import render, redirect
from django.core.paginator import Paginator

from intranet.components.core import SparkLine
from intranet.components.core import BarChart
from intranet.auth.decorators import login_required
from intranet.messages import add_error_message, add_success_message
from . import core
from . import dbraw
from . import links
from . import models


PAGE_SIZE = 25


def get_page(request) -> int:
    '''Devuelve el número de página, para los listados paginados.

    Espera que el número de página se haya pasado con el nombre
    ``p`` o ``page``.

    Params:

        ``request`` : El objeto ``request`` pasado a la vista.

    Returns:

        El número de la página, si se ha indicado, o ``1`` en caso
        contrario.

    '''
    try:
        num_page = int(request.GET.get('p', '1'))
        num_page = int(request.GET.get('page', num_page))
        return num_page
    except ValueError:
        return 1


def _get_links_per_site(site):
    return {
        'a_site_queue': links.a_site_queue(site),
        'a_site_last': links.a_site_last(site),
        'a_site_errors': links.a_site_errors(site),
        'a_site_scheduled': links.a_site_scheduled(site),
        'a_site_no_links': links.a_site_no_links(site),
        }


@login_required
def homepage(request):
    """Página de inicio: Relación de sites.
    """
    return render(request, 'spidercheck/homepage.html', {
        'titulo': "Spidercheck homepage",
        'sites': models.Site.get_all_sites(),
    })


@login_required
def site_detail(request, site):
    progress_hour = dbraw.get_hour_progress(site)
    sparkline = SparkLine(request, data=list(progress_hour.values()))
    versiones = BarChart(
        request,
        data=site.count_values('version'),
        label='Versiones',
        )
    scheduled = site.all_scheduled_pages()
    return render(request, 'spidercheck/site_detail.html', {
        'titulo': f'Site {site.name}',
        'site': site,
        'num_pages': site.pages.count(),
        'num_errores': site.pages_with_errors().count(),
        'num_queued': site.all_queued_pages().count(),
        'num_no_links': site.pages.filter(is_linkable=False).count(),
        'num_processed': site.pages.filter(is_checked=True).count(),
        'scheduled': scheduled,
        'num_scheduled': scheduled.count(),
        'progress_hour': progress_hour,
        'sparkline': sparkline,
        'versiones': versiones,
        'links': _get_links_per_site(site),
    })


@login_required
def site_errors(request, site):
    num_page = get_page(request)
    errors = site.pages_with_errors()
    paginator = Paginator(errors, PAGE_SIZE)
    return render(request, 'spidercheck/site_errors.html', {
        'titulo': f'Site {site.name} - Errores',
        'site': site,
        'num_errors': errors.count(),
        'num_page': num_page,
        'num_pages': site.pages.count(),
        'page': paginator.page(num_page),
    })


@login_required
def site_queue(request, site):
    num_page = get_page(request)
    pages = site.all_queued_pages()
    paginator = Paginator(pages, PAGE_SIZE)
    return render(request, 'spidercheck/site_queue.html', {
        'titulo': f'Site {site.name} - Cola',
        'site': site,
        'num_page': num_page,
        'num_pages': pages.count(),
        'page': paginator.page(num_page),
    })


@login_required
def site_last(request, site):
    num_page = get_page(request)
    pages = site.all_checked_pages()
    paginator = Paginator(pages, PAGE_SIZE)
    return render(request, 'spidercheck/site_last.html', {
        'titulo': f'Site {site.name} - Cola',
        'site': site,
        'num_page': num_page,
        'num_pages': pages.count(),
        'page': paginator.page(num_page),
    })


@login_required
def site_no_links(request, site):
    not_linkable_pages = site.pages.exclude(is_linkable=True)
    num_pages = not_linkable_pages.count()
    return render(request, 'spidercheck/site_no_links.html', {
        'titulo': f'Páginas no enlazables {site} ({num_pages})',
        'site': site,
        'num_pages': num_pages,
        'pages': not_linkable_pages,
    })


@login_required
def site_scheduled(request, site):
    scheduled = site.all_scheduled_pages()
    return render(request, 'spidercheck/site_scheduled.html', {
        'titulo': f'Site {site.name} - Páginas priorizadas',
        'site': site,
        'scheduled': scheduled,
        'num_pages': scheduled.count(),
        })


@login_required
def site_search(request, site):
    query = request.GET.get('q', '')
    pages = list(site.search(query)) if query else []
    return render(request, 'spidercheck/site_search.html', {
        'titulo': 'Búsqueda por patrones de URL',
        'site': site,
        'query': query,
        'pages': pages,
    })


@login_required
def site_orphans(request, site):
    num_page = get_page(request)
    orphans = dbraw.load_paginas_huerfanas(site.pk)
    paginator = Paginator(orphans, PAGE_SIZE)
    total_pages = len(orphans)
    return render(request, 'spidercheck/site_orphans.html', {
        'titulo': f'Páginas huérfanas en {site} ({total_pages})',
        'site': site,
        'num_page': num_page,
        'num_pages': len(orphans),
        'page': paginator.page(num_page),
    })


@login_required
def detail_page(request, page):
    return render(request, 'spidercheck/detail_page.html', {
        'titulo': f'Página {page.id_page} de {page.site.name}',
        'page': page,
    })


@login_required
def page_check(request, page):
    result = core.check_page(page)
    if result:
        add_success_message(
            request.session.id_usuario,
            f'La página {page.pk} se ha vuelto a comprobar: {result}',
            )
    else:
        add_error_message(
            request.session.id_usuario,
            f'La página {page.pk} sigue dando error: {result}',
            )
    return redirect(links.a_detalle_pagina(page))


@login_required
def toogle_is_linkable(request, page):
    page.is_linkable = not page.is_linkable
    if not page.is_linkable:
        counter, _ = models.Link.objects.filter(to_page=page.pk).delete()
        if counter > 0:
            id_usuario = request.session.id_usuario
            add_success_message(
                id_usuario,
                f'Se han eliminado {counter} enlaces',
                )
    page.save()
    return redirect(links.a_detalle_pagina(page))


@login_required
def page_delete(request, page):
    assert request.method == 'POST'
    assert page.can_be_deleted()
    site = page.site
    page.delete()
    return redirect(links.a_detalle_site(site))


def site_expunge(request, site):
    assert request.method == 'POST'
    id_usuario = request.session.id_usuario
    id_pages = [int(_) for _ in request.POST.getlist('id_pages')]
    counter = 0
    for page in models.Page.objects.filter(id_page__in=id_pages, site=site):
        site = page.site
        if page.can_be_deleted():
            page.delete()
            counter += 1
        else:
            add_error_message(id_usuario, f'La página {page} no ha podido ser borrada')
    add_success_message(id_usuario, f'Borradas {counter} páginas de {site}')
    return redirect(links.a_site_orphans(site))


def site_expunge_all(request, site):
    assert request.method == 'POST'
    id_usuario = request.session.id_usuario
    orphans = dbraw.load_paginas_huerfanas(site.pk)
    counter = 0
    for page in orphans:
        if page.can_be_deleted():
            page.delete()
            counter += 1
        else:
            add_error_message(id_usuario, f'La página {page} no ha podido ser borrada')
    add_success_message(id_usuario, f'Borradas {counter} páginas')
    return redirect(links.a_detalle_site(site))
