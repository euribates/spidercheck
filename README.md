## Spidercheck

![Spidercheck](docs/spidercheck-icon.svg)

**Spiderchech** es una araña o `rastreador web`_ pensado para realizar
pruebas mediante una estrategia de caja negra. Puede indexar diferentes
*sites* o *webs* de forma independiente.

Spidercheck inspecciona las páginas de un *web site* de forma metódica y
automatizada. Empieza visitando una URL inicial, identifica y normaliza
los enlaces en dichas páginas y los añade a la lista de URL pendientes
de visitar, de acuerdo a un determinado conjunto de reglas.

La operación normal es: obtiene una URL del listado de direcciones
pendiente de analizar, la descarga, analiza la página y busca enlaces a
páginas nuevas. Todas los enlaces que encuentre y que no hayan sido
descubiertos antes se añaden a la lista de páginas pendientes.

Spidercheck incluye la posibilidad de añadir plugins_ o
complementos que permitan realizar diferentes procesos en cada página o
fichero analizado. Entre las tareas que podríamos implementar con esta
funcionalidad estarían:

- Crear un índice, con el propósito de implementar una sistema de búsquedas.

- Copia o archivado de un _web site_

- Analizar los enlaces de un sitio para buscar _links_ rotos.

- Recolectar y compilar información de un cierto tipo, que estuviera
  distribuido entre las páginas del site.

Una _app_ de [Django](https://www.djangoproject.com/) para comprobar los enlaces internos de una web.
