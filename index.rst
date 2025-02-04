.. meta::
   :description: Spidercheck : Rastreador de sitios web
   :keywords: spider, crawler, web

Spidercheck
=======================================================================

**Spiderchech** es una araña o `rastreador web`_ pensado para realizar
pruebas mediante una estrategia de caja negra. Puede indexar diferentes
*sites* o webs de forma independiente.

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

- Copia o archivado de un *web site*

- Analizar los enlaces de un sitio para buscar *links* rotos.

- Recolectar y compilar información de un cierto tipo, que estuviera
  distribuido entre las páginas del *site*.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   docs/definitions
   docs/database-schema
   docs/procesos


.. _plugins: https://es.wikipedia.org/wiki/Complemento_(inform%C3%A1tica)
.. _rastreador web: https://es.wikipedia.org/wiki/Ara%C3%B1a_web
