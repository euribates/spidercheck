#!/usr/bin/env python3

from typing import Union
import time
from urllib.parse import urlparse
import logging
import sys

import requests

from comun.fechas import just_now
from comun.results import Success, Failure

from spidercheck.models import Page
from spidercheck.models import Site
from spidercheck.models import Value
from spidercheck.plugins import registry

from . import webparser


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.WARNING)
_logger.handlers.append(logging.StreamHandler(sys.stderr))
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_text_from_url(url):
    try:
        req = requests.get(url, allow_redirects=True)
        if 'content-length' not in req.headers:
            req.headers['content-length'] = len(req.text)
        return req.headers, req.text
    except IOError as err:
        return False, 503, f"Conexion error: {err}", {}


def get_content_type(headers):
    value = headers.get('content-type', '')
    if value and ';' in value:
        value, _ = value.split(';', 1)
    return value.lower()


def get_content_length(headers):
    value = headers.get('content-length', '0')
    return int(value)


def content_is_html(headers):
    content_type = get_content_type(headers)
    return content_type == 'text/html'


def _run_plugins(page, headers, body):
    values = {}
    failures = []
    for name, plugin_process in registry.get_all_plugins():
        try:
            result = plugin_process(page, headers, body)
            if result:
                values.update(result)
        except Exception as err:
            failures.append(f'{name}: {err}')
    antes = set([v.name for v in page.values.all()])
    despues = set(values)
    a_borrar = antes - despues
    if a_borrar:
        page.values.filter(name__in=a_borrar).delete()
    for name in values:
        Value.upsert(page, name, values[name])
    if failures:
        return Failure('Error al ejecutar los plug-ins:\n' + '\n - '.join(failures))
    return Success(values)


def _update_links(page, body):
    """
    Actualiza los enlaces de una página.

    Params:

        - page (Page) : La página cuyos enlaces estamos actualizando.

        - body (str) : El texto de la página.

    Returns:

        Una tupla con dos listas, la primera, los enlaces borrados, la segunda,
        los enlaces añadidos. Si no hay cambios en la página, debería ser dos
        listas vacias.

    """
    before_links = {p.to_page.pk for p in page.outgoing_links.all()}
    after_links = set({})
    for new_url in page.get_all_valid_links(body):
        target_page, created = self.site.add_page(new_url)
        if target_page.is_linkable:
            Link.objects.get_or_create(from_page=self, to_page=target_page)
            after_links.add(target_page.pk)
    to_remove_links = before_links - after_links
    to_add_links = after_links - before_links
    if to_remove_links:
        qset = (
            Link.objects
            .filter(from_page=self)
            .filter(to_page__in=to_remove_links)
            )
        qset.delete()
    return to_remove_links, to_add_links


# --[ Public API ]-----------------------------------------------------


def load_site(name):
    return Site.load_site_by_name(name)


def load_page(name, id_page):
    site = Site.load_site_by_name(name)
    return site.load_page(id_page)


def find_urls_by_pattern(site, pattern, use_regex=False):
    yield from site.search(pattern, use_regex)


def check_page(page) -> Union[Success, Failure]:
    page.checked_at = just_now()
    page.is_checked = True
    url = page.get_full_url()
    start_time = time.time()
    result = page.is_valid()
    if result.is_failure():
        page.status = int(result.code)
        page.error_message = result.error_message
        page.check_time = time.time() - start_time
        page.save()
        return Failure(f'Error al comprobar {url}: {result}')

    response = result.value
    page.status = response.status_code
    page.content_type = get_content_type(response.headers)
    page.size_bytes = get_content_length(response.headers)
    page.check_time = time.time() - start_time
    page.save()
    is_html = content_is_html(response.headers)
    if is_html:
        is_local = page.site.is_local(response.url)
        if is_local:
            headers, body = get_text_from_url(url)
            if webparser.is_valid_html(body):
                deleted_links, added_links = _update_links(page, body)
                plugins_phase = _run_plugins(page, headers, body)
                return Success(
                    f'Comprobando {url}'
                    f' Enlaces nuevos: {len(added_links)}'
                    f' Enlaces Borrados: {len(deleted_links)}'
                    f' Plugins: {"✓" if plugins_phase else "𐄂"}'
                    )
            else:
                page.status = 418 # I'm a TeaPot
                msg = f'La URL {url} debería ser HTML, pero no lo parece'
                page.error_message = msg
                page.save()
                return Failure(msg)
        else:
            page.outgoing_links.all().delete()
    return Success(f'Comprobando {url}')


def init_site(url, name="default"):
    """Crea un nuevo site con el nombre y url indicado.

    Puede elevar la excepción ``ValueError`` si la pasamos el nombre
    de un *site* que ya existe en la base de datos. Crea una instancia
    de ``Page`` vinculada con este *site* que será la frontera inicial.

    Params:

        - url (str): La *URL* semilla.

        - name (str): El nombre que queremos asignarle al site.

    Returns:

        Una instancia de ``Site``.

    """
    _logger.info("Creating site %s for URL %s", name, url)
    if Site.load_site_by_name(name):
        raise ValueError(f"Error: El site {name} ya existe")
    info = urlparse(url)
    _logger.info(" - Scheme: %s", info.scheme)
    _logger.info(" - Netloc: %s", info.netloc)
    _logger.info(" - Path: %s", info.path)
    site = Site(
        name=name,
        scheme=info.scheme,
        netloc=info.netloc,
        path=info.path,
    )
    site.save()
    initial_page = Page(
        site=site,
        subpath=info.path,
        is_checked=False,
        status=-1,
        )
    initial_page.save()
    _logger.info(f"Site created with id: {site.pk}")
    return site


def reset_site(name):
    """Reinicializa un site, como si estuviera recien creado.
    """
    site = Site.load_site_by_name(name)
    if not site:
        raise ValueError(f"No existe ningun site llamado {name}")
    site.pages.all().delete()
    site.add_page(site.path)
    return site


def check_site(site, num=1):
    """Generador de paginas analizadas.

    Devuelve una secuencia de tuplas de tres valores:

     - La URL analizada

     - Un flag indicando si la solicitud de la URL ha tenido
       éxito o no

     - El número de enlaces nuevos descubiertos (Si procede, es decir,
       si el contenido es de tipo `text/html`)

    El parámetro `num` indica el número máximo de enlaces a
    comprobar. Por defecto vale uno.

    Nota: Para no sobrecargar al servidor, es responsabilidad del llamador
    el establecer una pausa entre las distintas solicitudes. Se sugiere esperar
    al menos 2 segundos entre cada petición.
    """
    page = site.next_page_to_check()
    while page and num > 0:
        yield check_page(page)
        num -= 1
        page = site.next_page_to_check()
