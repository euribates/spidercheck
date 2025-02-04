#!/usr/bin/env python3

import time
import logging

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from utils.heartbeats import heartbeat
from spidercheck.models import Site
from spidercheck.plugins import registry
from spidercheck.core import (
    load_site,
    check_site,
    check_page,
    find_urls_by_pattern,
    load_page,
    init_site,
    reset_site,
)


OK = "[green]✓[/green]"
WAITING = "[italic yellow]\u001b[/]"
ERROR = "[red]✖[/red]"


def as_bool(value):
    return OK if value else ERROR


def as_status_code(status_code):
    if 200 <= status_code < 300:
        return f"[green]{status_code}[/green]"
    return f"[red]{status_code}[/red]"


NO_ERROR = 0
ERR_INIT_FAILURE = 1
ERR_RESET_FAILURE = 2
ERR_CHK_FAILURE = 3
ERR_INVALID_PAGE_ID = 4
ERR_BROKEN_LINK = 5

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class Command(BaseCommand):

    console = Console()
    help = (
        'Spidercheck CLI\n'
        'Opciones:\n\n'
        ' - init:    Crear un site con una url base asociada\n'
        ' - reset:   Reinicializar un site al estado inicial\n'
        ' - last:    Mostrar las últimas páginas analizadas\n'
        ' - queue:   Mostrar la cola de URLs pendientes de analizar\n'
        '            de un site\n'
        ' - status:  Mostrar el estado general de un site\n'
        ' - check:   Analizar y procesar la siguiente URL\n'
        ' - delete:  Borrar una página de la base de datos\n'
        ' - find:    Buscar en las URLs procesadas por expresión regular\n'
        ' - show:    Mostrar información sobre una página\n'
        ' - recheck: Analizar y procesar el siguiente enlace roto\n'
        '\n'
    )

    def add_arguments(self, parser):
        self.parser = parser
        self.parser.usage = '[python] ./manage.py spidercheck [orden]'
        self.parser.add_argument(
            '--verbose',
            help='Muestra más detalles de la acción',
            action='store_true',
            )

        subparsers = parser.add_subparsers(help='opciones', dest='action')
        # init
        init_parser = subparsers.add_parser("init")
        init_parser.add_argument(
            '--name',
            help='Reference name for site to check',
            default='default',
        )
        init_parser.add_argument(
            'url',
            help='URL to check',
            default="http://localhost/",
        )
        init_parser.set_defaults(func=self.cmd_init)

        # Reset
        reset_parser = subparsers.add_parser(
            "reset",
            help="Restablecer un site al estado inicial, borrando el índice",
        )
        reset_parser.add_argument(
            '--name',
            help='Reference name for site to reset',
            default='default',
        )
        reset_parser.set_defaults(func=self.cmd_reset)

        # errors
        errors_parser = subparsers.add_parser("errors")
        errors_parser.add_argument(
            '--name',
            help='Muestra enlaces con errores de un site',
            default='default',
        )
        errors_parser.set_defaults(func=self.cmd_errors)

        # queue
        queue_parser = subparsers.add_parser("queue")
        queue_parser.add_argument(
            '--name',
            help='Show queued jobs for site',
            default='default',
        )
        queue_parser.add_argument(
            '--num',
            type=int,
            help='Número de entradas en la cola a mostrar (por defecto 10)',
            default='10',
        )
        queue_parser.set_defaults(func=self.cmd_queue)

        # last
        last_parser = subparsers.add_parser("last")
        last_parser.add_argument(
            '--name',
            help='Muestras las últimas páginas analizadas del site',
            default='default',
        )
        last_parser.add_argument(
            '--num',
            type=int,
            help='Número de páginas a mostrar (por defecto 10)',
            default='10',
        )
        last_parser.set_defaults(func=self.cmd_last)

        # delete
        delete_parser = subparsers.add_parser("delete")
        delete_parser.add_argument(
            '--name',
            help='Nombre del site a comprobar (Si no se especifica, default)',
            default='default',
        )
        delete_parser.add_argument("ids", nargs="+", type=int)
        delete_parser.set_defaults(func=self.cmd_delete)

        # check
        check_parser = subparsers.add_parser("check")
        check_parser.add_argument(
            '--name',
            help='Nombre del site a comprobar (Si no se especifica, default)',
            default='default',
        )
        check_parser.add_argument(
            '--num',
            type=int,
            help='Número de enlaces a comprobar',
            default='1',
        )
        check_parser.add_argument(
            '--gap',
            type=int,
            help='Número de segundos entre comprobaciones',
            default='2',
        )
        check_parser.set_defaults(func=self.cmd_check)

        # Recheck
        recheck_parser = subparsers.add_parser("recheck")
        recheck_parser.add_argument(
            '--id',
            help='Identificador de la página a comprobar',
            default='0',
        )
        recheck_parser.add_argument(
            '--name',
            help='Nombre del sitio a comprobar',
            default='default',
        )
        recheck_parser.set_defaults(func=self.cmd_recheck)

        # status
        status_parser = subparsers.add_parser("status")
        status_parser.add_argument('--name', help='Shows site info', default='default')
        status_parser.set_defaults(func=self.cmd_status)
        # find
        find_parser = subparsers.add_parser("find")
        find_parser.add_argument('pattern', help='Patrón a usar para la búsqueda')
        find_parser.add_argument('--name', help='Shows site info', default='default')
        find_parser.add_argument('--regex', action='store_true', help='Use regular expressions')
        find_parser.set_defaults(func=self.cmd_find)
        # show
        show_parser = subparsers.add_parser("show")
        show_parser.add_argument('--name', help='Nombre del site', default='default')
        show_parser.add_argument(
            'id_page',
            help='Id. de la página de la cual se quiere mostrar información',
            type=int,
            )
        show_parser.set_defaults(func=self.cmd_show)
        # plugins
        show_plugins = subparsers.add_parser("plugins")
        show_plugins.set_defaults(func=self.cmd_plugins)

    def out(self, *args, sep=' ', end="\n"):
        outcome = sep.join([str(_) for _ in args])
        self.console.print(outcome, end=end)

    def warning(self, msg):
        self.out(Panel("[red]Aviso[/red]\n{msg}"))

    def success(self):
        self.out(OK)

    def failure(self, msg):
        self.out(f"{ERROR} [red bold]{msg}[/]")

    def cmd_init(self, options):
        name = options['name']
        url = options['url']
        self.out(f'Creando site {name} para la URL {url}', end=' ')
        try:
            init_site(url, name)
            self.success()
        except ValueError as err:
            self.failure(err)

    def cmd_status(self, options):
        sites = list(Site.get_all_sites())
        if not sites:
            self.warning(
                "No hay ningún site registrado. Use el comando:\n\n"
                "    init <base url> [--name <site name>] para crear\n\n"
                " un nuevo site a analizar. Si no se especifica\n"
                " nombre, el site se llamará «default»."
            )
        table = Table(show_header=True, header_style="bold", title='Sites')
        table.add_column("Name")
        table.add_column("URL", justify="left")
        table.add_column("Encontradas", justify="right")
        table.add_column("En cola", justify="right")
        table.add_column("Errores", justify="right")
        table.add_column("Progreso", justify="right")
        for site in sites:
            table.add_row(
                site.name,
                site.url(),
                str(site.pages.count()),
                str(site.all_queued_pages().count()),
                str(site.pages_with_errors().count()),
                f'{site.progress():.2f}%',
                )
        self.console.print(table)

    def cmd_plugins(self, options):
        table = Table(show_header=True, header_style="bold", title='Plugins')
        table.add_column("Name")
        table.add_column("Status", justify="left")
        table.add_column("function", justify="left")
        for name, _functor in registry.get_all_plugins():
            table.add_row(
                name,
                as_bool(_functor is not None),
                _functor.__doc__,
                )
        self.console.print(table)

    def cmd_reset(self, options):
        name = options['name']
        self.out(f'Reinicializando site {name}', end=' ')
        try:
            reset_site(name)
            self.success()
        except ValueError as err:
            self.failure(err)

    def cmd_show(self, options):
        name = options['name']
        id_page = options['id_page']
        page = load_page(name, id_page)
        if page:
            self.out(f"Id. page        : {page.pk}")
            self.out(f"URL             : {page.get_full_url()}")
            self.out(f"Tamaño (bytes)  : {page.size_bytes}")
            self.out(f"Check           : {OK if page.is_checked else WAITING}")
            for value in page.values.all():
                self.out(f"{value.name:<15} : {value.value}")
            outgoing_links = list(page.outgoing_links.all())
            if outgoing_links:
                self.out('Esta página enlaza a:')
                for link in outgoing_links:
                    self.out(f' - {link.to_page.pk}: {link.to_page.get_relative_url()}')
            incoming_links = list(page.incoming_links.all())
            if incoming_links:
                self.out('Esta página es enlazada desde:')
                for link in incoming_links:
                    self.out(f' - {link.from_page.pk}: {link.from_page.get_relative_url()}')
        else:
            raise CommandError(f"Imposible cargar la página {id_page} del site {name}")

    def cmd_errors(self, options):
        name = options['name']
        site = Site.load_site_by_name(name)
        self.out(f"Errores encontrados en {site} ({site.url()})")
        all_errors = site.pages_with_errors()
        num_errores = all_errors.count()
        if num_errores == 0:
            self.out(f"Este site no contiene por ahora ninguna enlace roto {OK}")
            return

        title = f"Hay {num_errores} errores detectados"
        table = Table(show_header=True, header_style="bold", title=title)
        table.add_column("Id")
        table.add_column("URL")
        table.add_column("Message")
        table.add_column("Checked at", justify="right")
        table.add_column("Status code", justify="right")
        for page in all_errors:
            table.add_row(
                str(page.id_page),
                page.get_relative_url(),
                page.error_message,
                str(page.checked_at),
                as_status_code(page.status),
            )
        self.console.print(table)

    def cmd_last(self, options):
        name = options['name']
        num = options.get('num', 10)
        site = Site.load_site_by_name(name)
        table = Table(show_header=True, header_style="bold", title="Last links")
        table.add_column("Id")
        table.add_column("URL")
        table.add_column("Title")
        table.add_column("Checked at", justify="right")
        table.add_column("Is ok", justify="right")
        for i, page in enumerate(site.all_checked_pages()):
            table.add_row(
                str(page.pk),
                page.get_relative_url(),
                page.get_value('title', default=''),
                str(page.checked_at),
                as_bool(page.is_ok()),
                )
            if i >= num:
                break
        self.console.print(table)

    def cmd_queue(self, options):
        name = options['name']
        num = options.get('num', 10)
        site = Site.load_site_by_name(name)
        queue_size = site.all_queued_pages().count()
        title = f'Queue for {name} ({queue_size} pages)'
        table = Table(show_header=True, header_style="bold", title=title)
        table.add_column("Id")
        table.add_column("URL", justify="left")
        table.add_column("Waiting time", justify="right")
        for i, page in enumerate(site.all_queued_pages()):
            table.add_row(
                str(page.pk),
                page.get_relative_url(),
                str(page.waiting_time()),
                )
            if i >= num:
                break
        self.console.print(table)

    def cmd_find(self, options):
        name = options['name']
        site = load_site(name)
        if not site:
            self.failure(f'[red]Error:[/] No existe el site [red]{name}[/]')
            return
        pattern = options['pattern']
        use_regex = options.get('regex', False)
        self.out(f'Buscando por el patrón [green]{pattern}[/]')
        table = Table(show_header=True, header_style="bold")
        table.add_column("Id")
        table.add_column("URL", justify="left")
        table.add_column("Checked", justify="right")
        table.add_column("Status", justify="right")
        for page in find_urls_by_pattern(site, pattern, use_regex=use_regex):
            table.add_row(
                str(page.pk),
                page.get_relative_url(),
                OK if page.is_checked else WAITING,
                as_status_code(page.status),
                )
        self.console.print(table)

    def cmd_check(self, options):
        name = options['name']
        site = load_site(name)
        if not site:
            self.failure(f'No existe el site [bold]{name}[/]')
            return
        num = options['num']
        gap = options['gap']
        for result in check_site(site, num):
            if self.is_verbose:
                self.out(str(result))
            if num > 1:
                time.sleep(gap)
        heartbeat()

    def cmd_recheck(self, options):
        name = options['name']
        site = load_site(name)
        if not site:
            self.failure(f'No existe el site [bold]{name}[/]')
            return
        id_page = int(options.get('id', 0))
        if id_page == 0:
            page = site.next_page_to_check()
        else:
            page = load_page(site, id_page)
            if not page:
                self.failure('La página indicada no existe')
                return
        result = check_page(page)
        if self.is_verbose:
            self.out(f'Comprobando de nuevo {page}: {result}')
            for value in page.values.all():
                self.out(f" ▸ {value.name:<26} : {value.value}")
            outgoing_links = list(page.outgoing_links.all())
            self.out(f' ▸ Total Enlaces de salida    : {len(outgoing_links)}')
            incoming_links = list(page.incoming_links.all())
            self.out(f' ▸ Total Enlaces de entrada   : {len(incoming_links)}')
        heartbeat()

    def cmd_delete(self, options):
        name = options['name']
        for id_page in options['ids']:
            page = load_page(name, id_page)
            if page:
                self.success(f'Borrar la página [bold]{page}[/]')
            else:
                self.failure(f'La página [bold]{id_page}[/] no existe')

    def handle(self, *args, **options):
        self.is_verbose = options.get('verbose', False)
        if 'func' in options:
            action = options['func']
            action(options)
        else:
            self.out(self.parser.description)
            self.out(f"Use:\n\t{self.parser.usage}")
