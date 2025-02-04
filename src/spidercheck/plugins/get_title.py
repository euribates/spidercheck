#!/usr/bin/env python3

"""
## Ejemplo de plugin.

Para hacer un _plugin_, tenemos que escribir una función
con, como mínimo, una función python válida, y dicha
functión tiene que cumplir las siguientes características:

    - Debe tener el nombre `process`.

    - Debe estar incluida en un módulo, que debe estar
      guardado en en la carpeta `plugins`.

    - Debe aceptar tres parámetros por posición,
      en el siguiete orden:

        - `url`: La dirección url que está siendo comprobada

        - `headers`: Las cabeceras obtenidas de la petición

        - `body`: El cuerpo de la respuesta obtenida de la petición

    - Debe devolver un diccionario con los datos adicionales
      que queremos asociar a esta `url`.

      Puede ser un diccionario vacio,
      si no nos interesa aportar ninguna información nueva.

En este ejemplo, se devuelve el contenido de la etiqueta `title`,
si se encuentra en el cuerpo de la página. Si no se encuentra
se devuelve un diccionario vacio.

Los otros dos parámetros --`url` y `header`-- son ignorados, en
este ejemplo, pero aun así, la función debe aceptarlos.
"""

from bs4 import BeautifulSoup

from spidercheck.seqtools import first


def process(_page, _headers, body):
    '''Extraer el título de las páginas'''
    soup = BeautifulSoup(body, 'html.parser')
    page_title = first(soup.find_all('title'))
    if page_title:
        page_title = page_title.get_text().strip()
        return {'title': page_title}
    return {}
