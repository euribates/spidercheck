#!/usr/bin/env python3

from datetime import timedelta as TimeDelta
from typing import Union, Self, Optional, Iterator
from urllib.parse import urlunparse, urlparse, urljoin
from urllib.robotparser import RobotFileParser
import functools
import logging
import random
import re

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Count
from django.db.models.functions import Now
import requests

import fechas
from results import Success, Failure
from seqtools import first
from spidercheck.parser import LinkExtractor


TABLESPACE = 'spidercheck'

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class Site(models.Model):

    class Meta:
        db_table = f'"{TABLESPACE}"."site"'
        verbose_name = 'Sitio web'
        verbose_name_plural = 'Sitios web'
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=['scheme', 'netloc', 'path'],
                name='unique_url'
            ),
        ]

    id_site = models.BigAutoField(primary_key=True)
    name = models.SlugField(max_length=32, unique=True)
    scheme = models.CharField(max_length=8)
    netloc = models.CharField(max_length=128)
    path = models.CharField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def load_site_by_name(cls, name: str) -> Optional[Self]:
        """Carga una Instancia del site especificado por el nombre.

        Params:

            name (str): Nombre del site.

        Returns:

            La instancia indicada, o ``None`` si no existe ningúna con ese nombre.
        """
        try:
            return cls.objects.get(name=name)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_all_sites(cls) -> Iterator[Self]:
        """Iterador para todos los sites registrados.

        Returns:

            Un iterador que recorre todos los _sites_ definidos.
        """
        yield from cls.objects.all()

    def __str__(self) -> str:
        return self.name

    def url(self, path='') -> str:
        """Devuelve una URL absoluta.

        La URL está compuesta a partir de los campos `scheme`, `netloc`
        y del parámetro `path`. Si no se incluye el parámetro `path`, que es opcional,
        se devuelve la semilla del _site_.

        Params:

            path (str): Opcional. Una ruta relativa. Si no se especifica, se
            usara el campo `path`, por lo que obtendremos la semilla del _site_.
            Si se especifica la ruta, es responsabilidad del llamador comprobar
            que es una URL interna. PAra esto, ver el método `is_local`.

        Returns:

            Una url absoluta.
        """

        return urlunparse([
            self.scheme,
            self.netloc,
            path or self.path,
            '',
            '',
            '',
        ])

    def get_robots_txt(self):
        url = self.url('robots.txt')
        robot_parser = RobotFileParser()
        robot_parser.set_url(url)
        robot_parser.read()
        return robot_parser

    def progress(self):
        total = self.pages.count()
        checked = self.pages.exclude(is_checked=False).count()
        if total > 0:
            return round(checked * 100.0 / total, 2)
        return 0

    def all_queued_pages(self):
        qset = (
            self.pages
            .filter(is_checked=False)
            .order_by('created_at')
            )
        if qset.count() > 0:
            return qset
        return (
            self.pages
            .filter(is_checked=True)
            .order_by('checked_at')
            )

    def all_checked_pages(self):
        return (
            self.pages
            .filter(is_checked=True)
            .exclude(checked_at=None)
            .order_by('-checked_at')
        )

    def all_pending_pages(self):
        return (
            self.pages
            .exclude(is_checked=True)
            .order_by('-created_at')
        )

    def pages_with_errors(self):
        return (
            self.pages
            .filter(is_checked=True)
            .exclude(status__range=(200, 300))
            .order_by('-checked_at')
        )

    def all_scheduled_pages(self):
        return ScheduledPage.objects.filter(page__site_id=self.pk).all()

    def first_page_with_errors(self):
        return first(self.pages_with_errors())

    def next_page_to_check(self):
        """Devuelve la siguiente dirección en la forntera a comprobar,

        - Si hay páginas programadas (Vér modelo `ScheduledPage`) y ya se ha llegado
        el momento de procesarlas de nuevo, se devuelve la primera de ellas

        - Si hay páginas con errores, con una probabilidad del 50%, se intenta
        volver a procesar la página que más tiempo llava en la lista de páginas
        con errores.

        - Si no hay errores, o si, habiendolos, se decidió no volver a procesarlos,
        se devuelve la siguiente página en la forntera propiamente dicha.

        Returns:

            La siguiente página a ser procesada.
        """
        scheduled = first(
            self.all_scheduled_pages()
            .filter(watermark__lt=Now())
            )
        if scheduled:
            return scheduled.page
        if self.pages_with_errors().count() > 0 and random.random() <= 0.50:
            return self.pages_with_errors().last()
        if self.all_queued_pages().count() > 0:
            return self.all_queued_pages().first()
        return self.pages.all().order_by('checked_at').first()

    def is_local(self, url) -> bool:
        """Verdadero si la ruta pasada es local al *site*.

        Params:
            
            - url (Str): Una posible ruta dentro del site.

        Returns: 

            `True` si la ruta es interna, `False` en caso contrario.`
        """
        info = urlparse(url)
        if info.scheme and info.scheme != self.scheme:
            return False
        if info.netloc and info.netloc != self.netloc:
            return False
        return True

    def load_page(self, pk):
        try:
            return self.pages.get(pk=pk)
        except ObjectDoesNotExist:
            return None

    def load_or_create(self, subpath, params):
        """Devuelve una pagina del site si ya existe, o la crea si no.

        Este método busca en la base de datos una página que se
        corresponda, para el site, con la ruta y los parámetros pasados. Si
        la encuentra, devuelve dicha página. Si no existe, se crea y se
        devuelve. El objetivo es nunca crear la misma página dos veces en la
        base de datos.

        Params:

            subpath (str) : Ruta de la página.

            parmas (dict) : Un diccionario con los parámetros para dicha página,
                            si los hubiera.

        Returns:

            Una instancia de la clase `Page`.
        """
        found = first(self.pages.extra(
            where=["subpath = %s AND params = %s"],
            params=[subpath, params],
            ))
        if found:
            return found, False
        new_page = Page(
            site=self,
            subpath=subpath,
            params=params,
            )
        new_page.save()
        return new_page, True

    def add_page(self, url):
        info = urlparse(url)
        page, created = self.load_or_create(
            subpath=info.path,
            params=info.query,
        )
        if created:
            _logger.info("added new_url to check: %s", url)
        return page, created

    def search(self, query, use_regex=False):
        if use_regex:
            pat_re = re.compile(query, re.IGNORECASE)
            for page in self.pages.all().order_by('-status', 'pk'):
                url = page.get_relative_url()
                if pat_re.search(url):
                    yield page
        else:
            for page in self.pages.filter(subpath__icontains=query).order_by('-status', 'pk'):
                yield page

    @functools.lru_cache
    def get_excluded_subpaths(self):
        return {_.subpath for _ in self.excludes.all()}

    def count_values(self, name):
        queryset = (
            Value.objects
            .filter(name=name)
            .select_related('page')
            .filter(page__site=self)
            .order_by('name')
            .values('value')
            .annotate(num_pages=Count('*'))
            )
        return {
            v['value']: v['num_pages']
            for v in queryset.all()
            }


class Page(models.Model):

    class Meta:
        db_table = f'"{TABLESPACE}"."page"'
        verbose_name = 'Página'
        verbose_name_plural = 'Páginas'
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=['site', 'subpath', 'params'],
                name='unique_full_path'
            ),
        ]

    id_page = models.BigAutoField(primary_key=True)
    site = models.ForeignKey(
        Site,
        related_name='pages',
        on_delete=models.CASCADE,
    )
    subpath = models.CharField(
        max_length=280,
        default='',
        blank=True,
        null=True,
        )
    params = models.CharField(
        max_length=1024,
        default='',
        blank=True,
        null=True,
        )
    is_checked = models.BooleanField(default=False)
    checked_at = models.DateTimeField(
        'Last time checked',
        default=fechas.EPOCH,
        help_text='Timestamp de comprobación',
        )
    #: Segundos empleados en procesar está página
    check_time = models.FloatField(
        default=0.0,
        help_text='Segundos empleados en procesar esta página',
        )

    status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    size_bytes = models.BigIntegerField(default=0)
    content_type = models.CharField(max_length=32, default='')
    error_message = models.CharField(max_length=512, default='')
    is_linkable = models.BooleanField(default=True)

    @classmethod
    def load_page(cls, pk: int) -> Optional[Self]:
        """Obtiene la página indicada por su clave primaria, o `None` si no existe.
        ¨"""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            return None

    def get_all_valid_links(self, html_text: str) -> Iterable[str]:
        """Lista todos los enlaces encontrados en una página HTML.

        Si son enlaces externos, o están excluidos en el `robots.txt`,
        no se consideran válidas y no se incluyen den el resultado.

        Params:

            - html_text (str): Texto completo de la página.

        Returns:

            Un iterador que va devolviendo todos los enlaces internos válidos
            encontrados en el texto de la página.
        """
        parser = LinkExtractor()
        parser.feed(html_text)
        robot_parser = self.site.get_robots_txt()
        for link in parser.all_links():
            url = urljoin(self.get_full_url(), link)
            if url == self.get_full_url():
                continue
            if self.site.is_local(url) and robot_parser.can_fetch("*", link):
                link = urljoin(self.get_relative_url(), link)
                yield link

    def is_ok(self) -> bool:
        """verdadero si y solo si el código de respuesta está en el rango 2xx.

        Returns:

            `True` si el codigo de respuesta fue correcto (2xx) en la
            última comprobación.
        """
        return 200 <= self.status < 300

    def can_be_deleted(self) -> bool:
        """
        Devuelve verdadero (`True`) si la página puede ser borrada.

        Por ahora, la única condición que se comprueba es que no exista
        ninguna otra página que tenga a esta como destino.

        Returns:

            `True` si la página puede ser borrada.
        """
        return self.incoming_links.count() == 0

    def get_relative_url(self):
        path = urljoin(self.site.path, self.subpath)
        return urlunparse([
            '',
            '',
            path,
            '',
            self.params,
            '',
        ])

    def get_full_url(self):
        """Devuelve el URL completo de la página.

        Returns:

            Una url completa, incluyendo el esquema (`http` o `https`)
        """
        path = urljoin(self.site.path, self.subpath)
        return urlunparse([
            self.site.scheme,
            self.site.netloc,
            path,
            '',
            self.params,
            '',
        ])

    def is_valid(self) -> Union[Success, Failure]:
        """Comprueba si la página es correcta.

        Para ello, se realiza una petición de tipo `HEAD` al servidor, y
        se verifica que la respuesta sea correcta.

        Returns: 

            Una instancia de `Success` si es correcta, o una instancia
            de `Failure` en caso contrario.
        """
        url = self.get_full_url()
        status_code = -1
        try:
            req = requests.head(
                url,
                allow_redirects=True,
                headers={'Accept-Encoding': 'identity'},
                )
            status_code = req.status_code
            req.raise_for_status()
            return Success(req)
        except requests.exceptions.HTTPError as err:
            return Failure(str(err), code=status_code)

    def __str__(self) -> str:
        return self.get_full_url()

    def waiting_time(self) -> DeltaTime:
        """Devuelve el lapso de tiempo desde la última comprobación.
        
        Se utiliza para priorizar la frontera. Normalmente se comprueba
        la página que máß tiempo lleva sin ser comprobada.

        Returns:

            Un objeto de tipo `datetime.deltatime`, con el tiempo
            pasado desde la última actualización.

        """
        now = fechas.just_now()
        if self.checked_at:
            return now - self.checked_at
        return now - self.created_at

    def get_value(self, name, default='Desconocido/No aplica'):
        v = self.values.filter(name=name).first()
        return v.value if v else default

    def get_version(self):
        return self.get_value('version')

    def get_title(self):
        return self.get_value('title')

    def is_scheduled(self) -> bool:
        """Indica si la página está programada.

        Ver modelo `SchudelePage`. Las páginas programadas se actualizan
        de forma periodica, según un plazo de tiempo definido para
        cada página, saltandose el protocolo normal de prioridades.

        Returns:

            `True` si es una página programada.

        """
        return ScheduledPage.objects.filter(pk=self.pk).exists()

    def get_scheduled_rotation(self):
        assert self.is_scheduled()
        return ScheduledPage.objects.get(pk=self.pk).rotation



class Link(models.Model):
    """
    El modelo Link (Enlace).

    Este modelo almacena la relación que se establece entre dos páginas
    cuando una de ellas enlaza a la otra. Es una relación `N x N` entre
    la tabla `Page` y otra vez la tabla `Page`. Los campos de este
    modelo son: 
    
    - `id_link`: La clave primaría del enlace.
    
    - `from_page`: Clave foranea a la página de la que sale el enlace.

    - `to_page`: Clave foranea a la que se dirige en enlace.

    Existe una restricción que impide crear dos enlaces iguales, es
    decir, que se originen en una misma página y enlazan a otra página,
    también la misma. En otras palabras, que la información de que la
    página `A` enlaza con la página `B` solo está almacenada una vez en
    la base de datos.

    La definición de las claves foraneas provoca que en la clase `Page`
    se creen los atributos `outgoing_link` (Enlaces salientes) y
    `incoming_links` (enlaces entrantes).

    """

    class Meta:
        db_table = f'"{TABLESPACE}"."link"'
        verbose_name = 'Enlace'
        verbose_name_plural = 'Enlaces'
        ordering = ["from_page", "to_page"]
        constraints = [
            models.UniqueConstraint(
                fields=['from_page', 'to_page'],
                name='unique_from_to_page'
            ),
        ]

    id_link = models.BigAutoField(primary_key=True)
    from_page = models.ForeignKey(
        Page,
        related_name='outgoing_links',
        on_delete=models.CASCADE,
    )
    to_page = models.ForeignKey(
        Page,
        related_name='incoming_links',
        on_delete=models.CASCADE,
    )


class ValueManager(models.Manager):

    def get_by_natural_key(self, page, name):
        """Devolver el valor a partir de su clave natural.

        Params:

            - page (Page) : La página a la que está asociado el valor

            - name (str): El nombre del valor.

        Returns:
            
            La instancia de Value, o puede elevar una excepción de tipo
            `ObjectDoesNotExist` si no existe.

        """
        return self.get(page=page, name=name)


class Value(models.Model):
    """
    Valores asignados a páginas

    Spidercheck permite almacenar valores particulares para cada
    página. Estos valores se pueden conseguir de diferentes sitios, y
    el sistema de *plugins* permite guardar estos valores de forma
    fácil, solo tiene que devolver un diccionario con los nombres
    (claves) y valores que quiera almacenar.

    En la carpeta `pluging` hay algunos plugins por defecto que viene
    incluidos a modo de ejemplo. En `plugins/get_title.py`, por ejemplo,
    el plugin busca en el contenido de la página a ver si encuentra las
    etiquetas Html para el título. Si las encuentra, devuelve un
    diccionario con una única entrada, siendo la clave `title` y el
    contenido el encontrado en la página. Spidercheck almacena este
    valor, vinculado a la página, en esta tabla.

    Los campos de este modelo son:

    - `id_value`:  Clave primaria

    - `page`: Clave foranea a la página asociada con este valor. La
      relación inversa en el modelo `Page` se llama `values`.

    - `name`: El nombre del valor, por ejemplo, `title`.

    - `value`: El valor, en forma de cadena de texto.

    La combinación de página (`page`) y nombre (`name`) forman una
    [clave natural](https://docs.djangoproject.com/fr/2.2/topics/serialization/#natural-keys),
    es decir, que para una página dada, soo puede tener un valor para un
    nombre dado. En nuestro ejemplo, una página solo puede tener un
    título.

    """

    class Meta:
        db_table = f'"{TABLESPACE}"."value"'
        verbose_name = 'Valor'
        verbose_name_plural = 'Valores'
        ordering = ["page", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=['page', 'name'],
                name='unique_value_for_page'
            ),
        ]

    id_value = models.BigAutoField(primary_key=True)
    page = models.ForeignKey(
        Page,
        related_name='values',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=64)
    value = models.CharField(max_length=2048)

    objects = ValueManager()

    def __str__(self):
        return f'{self.name}={self.value}'

    @classmethod
    def upsert(cls, page, name, value):
        """Añade/Modifica un valor asociado a una página.

        Params:

            `page`: La pagina, es decir, la instancia de `Page` a la que
            se vincula este valor.

            `name`: Nombre del valor. POr ejemplo, `title`.

            `value` : El valor a almacenar. Como intermenta se usa JSON,
            solo puede ser `None`, boleanos, numeros enteros o en coma
            flotante o cadenas de texto. Los valores de tipo *timestamp*
            no
            se pueden almacenar nativamente, 

        Returns:

            """
        _value, _ = cls.objects.get_or_create(page=page, name=name)
        _value.value = str(value)
        _value.save()
        return _value

    def natural_key(self) -> tuple[Page, str]:
        """Obtener los valores de la clave natural del valor.

        Returns:
            Una tupla con los valores de la clave natural de `Value`.

        """
        return (self.page, self.name)


class SheduledPageManager(models.Manager):

    def get_queryset(self):
        return (
            super().get_queryset()
            .select_related('page')
            .annotate(watermark=models.ExpressionWrapper(
                models.F('page__checked_at') + models.F('rotation'),
                output_field=models.DateTimeField(),
                ))
            )


class ScheduledPage(models.Model):
    """Páginas programadas

    El objetivo de este modelo es poder especiifcar determinadas páginas
    como páginas programadas (*Scheduled*). Estas págnas definen un
    lapso de tiempo, transcurrido el cual se saltan la prioridad normal 
    y se ponen las primeras en la frontera.

    Por ejemplo, si programamos la página de noticias (´/noticias/´), con
    una rotación de una hora, entonces, pasada una hora desde la última
    vez que se comprobó, la próxima página a ser comprobada será la de
    noticias, sin importar las páginas que estén en ese momento en la
    forntera. En otras palabras, la página de noticias se actualiza cada
    hora.

    Los campos definidos en este modelo son:

    - page
    - rotation
    - updated_at
    - created_at

    """

    class Meta:
        db_table = f'"{TABLESPACE}"."scheduled_page"'
        verbose_name = 'Página priorizada'
        verbose_name_plural = 'Páginas priorizadas'
        ordering = ['page__checked_at', 'updated_at', 'created_at']

    page = models.OneToOneField(
        Page,
        on_delete=models.CASCADE,
        primary_key=True,
        )
    rotation = models.DurationField(
        'Rotación (secs)',
        default=fechas.HALF_DAY,  # Dos veces al día
        help_text='Tiempo mínimo entre cada comprobación',
        )
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False) 

    objects = SheduledPageManager()

    def get_relative_url(self):
        return self.page.get_relative_url()

    def get_full_url(self):
        return self.page.get_full_url()
