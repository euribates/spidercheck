#!/usr/bin/env python3

"""
Módulo ``comun.fechas``
------------------------------------------------------------------------

funciones y utilidades para gestión de fechas.

La idea es usar siempre este módulo para todo lo relativo a trabajar con
fecha, *timestamps* (fechas y horas) y diferencias temporales.

Constantes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autodata:: comun.fechas.EPOCH
.. autodata:: comun.fechas.HALF_HOUR
.. autodata:: comun.fechas.ONE_HOUR
.. autodata:: comun.fechas.HALF_DAY
.. autodata:: comun.fechas.ONE_DAY
.. autodata:: comun.fechas.TWO_DAYS
.. autodata:: comun.fechas.ONE_MONTH


"""
from calendar import monthrange
from datetime import date as Date
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from html import escape
from typing import Optional
import functools
import re

from django.conf import settings
from pytz import timezone

# Constantes

#: Epoch Time
EPOCH = DateTime(1970, 1, 1, 0, 0, 0, 0)

#: Media hora, :math:`\frac{1}{2} hora = 30\times 60 s`
HALF_HOUR = TimeDelta(seconds=1800)

#: Una hora
ONE_HOUR = TimeDelta(hours=1)

#: Medio día (12 horas)
HALF_DAY = TimeDelta(hours=12)

#: Un día (24 horas)
ONE_DAY = TimeDelta(days=1)

#: Dos días (24 horas)
TWO_DAYS = TimeDelta(days=2)

#: Una semana (7 días)
ONE_WEEK = TimeDelta(days=7)

#: Aprox. 31 días
ONE_MONTH = TimeDelta(days=31)


def _datetime_now() -> DateTime:
    """
    Obtener la fecha y hora actual en la zona horaria indicada.

    Si no se especifica la zona horaria, se usará la especificada en el
    fichero de configuración de Django, en nuestro caso la zona horaria
    de Canarias.

    Esta función debería de usarse en lugar de:

    - ``datetime.datetime.now``

    - ``django.utils.timezone.now``

    - ``datetime.date.today``

    Returns:

        Una instancia de ``datetime.date``.

    """
    if settings.USE_TZ:
        zone_info = get_zone_info()
        result = DateTime.now(zone_info)
        return result.replace(tzinfo=None)
    return DateTime.now()


@functools.lru_cache
def get_zone_info():
    """Devuelve la zona horaria por defecto.
    """
    return timezone(settings.TIME_ZONE)


def just_now():
    """
    Devuelve un objeto ``datetime.datetime`` con la fecha y hora
    actuales, en la zona horaria por defecto.

    Returns:

        La fecha y hora actual

    """
    return _datetime_now()


def just_today():
    """
    Devuelve un objeto ``datetime.date`` con la fecha actual, en la zona
    horaria por defecto.
    """
    return _datetime_now().date()


def this_year():
    """
    Devuelve el año actual.
    """
    return _datetime_now().year


def next_year():
    """
    Devuelve el año siguiente al actual.
    """
    return this_year() + 1


def next_day(fecha: Date) -> Date:
    """
    Devuelve la fecha del dia siguiente al pasado como referencia
    """
    return fecha + ONE_DAY


def dmy(strfecha):
    for c in ('.', '/', '-'):
        if len(strfecha.split(c)) > 1:
            (d, m, y) = strfecha.split(c)
            return tuple(map(int, [y, m, d]))


def ymd(strfecha):
    return tuple(map(int, strfecha.split('-')))


def new_date(year=None, month=None, day=None):
    """Función que retorna una fecha a partir de los parámetos pasados.

    Si no se indica un parámetro, se usará el de la fecha actual.
    """
    hoy = _datetime_now().date()
    return Date(
        year or hoy.year,
        month or hoy.month,
        day or hoy.day
    )


nueva_fecha = new_date  # retrocompatibilidad


def new_date_and_time(year, month, day, hour=0, minute=0, second=0):
    """Función que retorna una fecha/hora a partir de los parámetos pasados.
    """
    zone_info = timezone(settings.TIME_ZONE) if settings.USE_TZ else None
    return DateTime(
        year,
        month,
        day,
        hour,
        minute,
        second,
        tzinfo=zone_info
    )


def next_month(fecha) -> Date:
    """Función que calcula el mes siguiente de la fecha dada.

    Calcula el día de la semana de ese mes y el número de días que tiene
    el mes.  Retorna una fecha con el año, mes y el mismo día de ese
    mes, si puede, y si no, el día más cercano.

    Por ejemplo, si le pasamos el 31 de enero, devolverá el 27 de
    febrero, o el 28 si el año es bisiesto. Si pasamos el 31 de marzo,
    devolverá el 30 de abril.

    Returns:

        Una fecha (Una instancia de ``datetimed.date``) desplazada
        en el futuro (más o menos) un mes.

    """
    year, month, day = (fecha.year, fecha.month, fecha.day)
    year, month = (year, month + 1) if month < 12 else (year + 1, 1)
    _, days = monthrange(year, month)
    day = min(days, day)
    return nueva_fecha(year, month, day)


def num_days(days=1) -> TimeDelta:
    """Obtener un ``timedelta`` con los días indicados.
    
    Parameters:

        days (int): Opcional. Número de días en el ``timedelta``. Si
           no se especica, un dia.

    Returns:

        Un objeto ``timedelta`` con los días indicados
        Si no se especifica, devuelve un ``timedelta`` de un día exacto.
    """
    return TimeDelta(days=days)


def num_seconds(seconds=3600) -> TimeDelta:
    """Obtener un ``timedelta`` con los segundos indicados.
    
    Parameters:

        seconds (int): Opcional. Número de segundos en el ``timedelta``.
           Si no se especica, sera de 5 minutos 
           (:math:`3600 s = 5\times 60 s`).

    Returns:

        Un objeto ``timedelta`` con los segundos indicados.
        Si no se espedifica, devuelve un ``timedelta`` de
        cinco minutos.

    """
    return TimeDelta(seconds=seconds)


def last_hours(size=24):
    now = just_now()
    for _ in range(size):
        yield (now.year, now.month, now.day, now.hour)
        now -= ONE_HOUR


def from_timestamp(num: float) -> DateTime:
    return DateTime.fromtimestamp(num)


# Date and Date/Time parsers

# PAtrones de parseo de fechas y fechas.horas

class BaseDateParser:

    PAT_DMY = re.compile(
        r'(?P<day>\d+)'
        r'[\\\/:\.,\- ]+'
        r'(?P<month>[a-zA-Z0-9]+)'
        r'[\\\/:\.,\- ]'
        r'(?P<year>\d\d\d\d)'
        r'$'
        )

    PAT_ISO8601_DATE_EXT = re.compile(
        r'(?P<year>\d{4})'
        r'-'
        r'(?P<month>\d{2})'
        r'-'
        r'(?P<day>\d{2})'
        r'$'
        )

    PAT_ISO8601_DATETIME_EXT_BASIC = re.compile(
        r'(?P<year>\d{4})'
        r'-'
        r'(?P<month>\d{2})'
        r'-'
        r'(?P<day>\d{2})'
        r'[ T]'
        r'(?P<hour>\d{2})'
        r':'
        r'(?P<minute>\d{2})'
        r':'
        r'(?P<second>\d{2})'
        r'(?:[\+\-]\d\d:\d\d)?'
        r'$'
        )

    PAT_ISO8601_DATE_BASIC = re.compile(
        r'(?P<year>\d{4})'
        r'(?P<month>\d{2})'
        r'(?P<day>\d{2})'
        r'$'
        )

    PAT_ISO8601_DATETIME_BASIC = re.compile(
        r'(?P<year>\d{4})'
        r'(?P<month>\d{2})'
        r'(?P<day>\d{2})'
        r'(?P<hour>\d{2})'
        r'(?P<minute>\d{2})'
        r'(?P<second>\d{2})'
        r'$'
        )

    PAT_RFC822_DATETIME = re.compile(
        r'(\w\w\w, )?'
        r'(?P<day>\d+)'
        r' '
        r'(?P<month>\w+)'
        r' '
        r'(?P<year>\d+)'
        r' '
        r'(?P<hour>\d+)'
        r':'
        r'(?P<minute>\d+)'
        r':'
        r'(?P<second>\d+)'
        r'.+'
        r'$'
        )

    PAT_RFC822_DATE = re.compile(
        r'(\w\w\w, )?'
        r'(?P<day>\d+)'
        r' '
        r'(?P<month>\w+)'
        r' '
        r'(?P<year>\d+)'
        r'$'
        )

    PAT_FECHA_COMPLETA = re.compile(
        r'(?P<day>\d+)'
        r' de '
        r'(?P<month>[a-zA-Z]+)'
        r' de '
        r'(?P<year>\d+)'
        r'$'
        )

    PAT_FECHA_HORA = re.compile(
        r'(?P<day>\d+)'
        r'-'
        r'(?P<month>\d+)'
        r'-'
        r'(?P<year>\d+)'
        r' '
        r'(?P<hour>\d\d)'
        r':'
        r'(?P<minute>\d\d)'
        r':'
        r'(?P<second>\d\d)'
        r'.'
        r'(\d+)'
        r'$'
        )

    PAT_DDMMYYYYHHMMSS = re.compile(
        r'(?P<day>\d\d?)'
        r'[/\-]'
        r'(?P<month>\d\d?)'
        r'[/\-]'
        r'(?P<year>\d\d\d\d)'
        r' '
        r'(?P<hour>\d+)'
        r':'
        r'(?P<minute>\d+)'
        r':'
        r'(?P<second>\d+)'
        r'$'
        )

    PAT_DDMMYYHHMMSS = re.compile(
        r'(?P<day>\d\d?)'
        r'[/\-]'
        r'(?P<month>\d\d?)'
        r'[/\-]'
        r'(?P<year>\d\d)'
        r' '
        r'(?P<hour>\d+)'
        r':'
        r'(?P<minute>\d+)'
        r':'
        r'(?P<second>\d+)'
        r'$'
        )

    PARSERS = [
        PAT_DMY,
        PAT_ISO8601_DATETIME_EXT_BASIC,
        PAT_ISO8601_DATETIME_BASIC,
        PAT_ISO8601_DATE_BASIC,
        PAT_ISO8601_DATE_EXT,
        PAT_RFC822_DATETIME,
        PAT_RFC822_DATE,
        PAT_FECHA_COMPLETA,
        PAT_FECHA_HORA,
        PAT_DDMMYYYYHHMMSS,
        PAT_DDMMYYHHMMSS,
        ]

    REVERSE_MONTH = {
        'JAN': 1, 'JANUARY': 1, 'ENE': 1, 'ENERO': 1,
        'FEB': 2, 'FEBRUARY': 2, 'FEBRERO': 2,
        'MAR': 3, 'MARCH': 3, 'MARZO': 3,
        'APR': 4, 'APRIL': 4, 'ABR': 4, 'ABRIL': 4,
        'MAY': 5, 'MAYO': 5,
        'JUN': 6, 'JUNE': 6, 'JUNIO': 6,
        'JUL': 7, 'JULY': 7, 'JULIO': 7,
        'AUG': 8, 'AUGUST': 8, 'AGO': 8, 'AGOSTO': 8,
        'SEP': 9, 'SEPTEMBER': 9, 'SEPTIEMBRE': 9,
        'OCT': 10, 'OCTOBER': 10, 'OCTUBRE': 10,
        'NOV': 11, 'NOVEMBER': 11, 'NOVIEMBRE': 11,
        'DEC': 12, 'DECEMBER': 12, 'DIC': 12, 'DICIEMBRE': 12,
        }


    def _to_year_month_day(self, _match):
        day = _match.group('day')
        month = _match.group('month')
        year = _match.group('year')
        day = int(day)
        if month.isdigit():
            month = int(month)
        else:
            month = self.REVERSE_MONTH[month.upper()]
        year = int(year)
        if year <= 100:
            year += 2000
        return year, month, day

    def _to_hour_minute_second(self, _match):
        hour = minute = second = 0
        try:
            hour = int(_match.group('hour'))
            minute = int(_match.group('minute'))
            second = int(_match.group('second'))
        except IndexError:
            pass
        return (hour, minute, second)


class DateParser(BaseDateParser):

    def __call__(self, texto: str) -> Optional[Date]:
        texto = texto.strip()
        if not texto:
            return None
        for patron in self.PARSERS:
            _match = patron.match(texto)
            if _match:
                year, month, day = self._to_year_month_day(_match)
                return Date(year, month, day)
        raise ValueError('Formato de fecha incorrecto: "{}"'.format(escape(texto)))


parse_date = DateParser()


class DateTimeParser(BaseDateParser):

    def __call__(self, texto: str) -> Optional[Date]:
        texto = texto.strip()
        if not texto:
            return None
        for patron in self.PARSERS:
            _match = patron.match(texto)
            if _match:
                year, month, day = self._to_year_month_day(_match)
                hour, minute, second = self._to_hour_minute_second(_match)
                return DateTime(year, month, day, hour, minute, second)
        raise ValueError('Formato de fecha/hora incorrecto: "{}"'.format(escape(texto)))


parse_datetime = DateTimeParser()
