.. meta::
   :description: Spidercheck : Rastreador de sitios web
   :keywords: spider, crawler, web
   

---
title: "Spidercheck : Rastreador de sitios web"
author: "M.D. Juan Ignacio Rodríguez de León <jileon@parcan.es>"
---

## Spidercheck

### Introducción

**Spiderchech** es una araña o [rastreador web](https://es.wikipedia.org/wiki/Ara%C3%B1a_web) pensado para realizar pruebas mediante una estrategia de caja negra. Puede indexar diferentes *sites* o webs de forma independiente.

Spidercheck inspecciona las páginas de un _web site_ de forma metódica y automatizada. Empieza visitando una URL inicial, identifica y normaliza los enlaces en dichas páginas y los añade a la lista de URL pendientes de visitar, de acuerdo a un determinado conjunto de reglas.

La operación normal es: obtiene una URL del listado de direcciones pendiente de analizar, la descarga, analiza la página y busca enlaces a páginas nuevas. Todas los enlaces que encuentre y que no hayan sido descubiertos antes se añaden a la lista de páginas pendientes.

Spidercheck incluye la posibilidad de añadir [_plugins_ o complementos](https://es.wikipedia.org/wiki/Complemento_(inform%C3%A1tica)) que permitan realizar diferentes procesos en cada página o fichero analizado. Entre las tareas que podríamos implementar con esta funcionalidad estarían:

- Crear un índice, con el propósito de implementar una sistema de búsquedas.

- Copia o archivado de un _web site_

- Analizar los enlaces de un sitio para buscar _links_ rotos.

- Recolectar y compilar información de un cierto tipo, que estuviera distribuido entre las páginas del site.

### definiciones e información general

Un rastreador web comienza con una lista de direcciones URL para visitar, llamado **semillas**. Como se comentó antes, Spidercheck, aunque empieza con una semilla con una única dirección, durante el proceso usa una lista de direcciones pendientes a rastrear, este conjunto de direcciones se llama **frontera de rastreo**.

Spiderchek **no es una araña de restreo general**, sino que está orientada a un único servidor web, o incluso a una sección de un servidor web. Por ello, y para evitar que siga los enlaces externos que podrían llevarle en a intentar rastrear tola la Internet, solo incluye en la frontera de rastreo las URL que están definidas debajo de la semilla inicial. Es decir, que si la semilla inicial empieza en `http://uvw.es/`, entonces un enlace a, por ejemplo, `http://uvw.es/about/` se considera un **enlace interno** y se añade a la frontera, pero un enlace a `http://xyz.es/` se considera **externo** y, por tanto, no se incluye.
 
El gran volumen de páginas implica también que el rastreador sólo puede descargar un número limitado de páginas en un tiempo determinado, por lo que necesita dar algún tipo de prioridad a sus descargas. Además, como las páginas pueden ser modificadas en el futuro, hay que tener en cuenta que incluso una página recién comprobada tendrá que ser analizada de nuevo en un futuro más o menos cercano.


### Modelo de base de datos

En Spidercheck hay 5 tablas/modelos:

- `Site`
- `Page`
- `Link`
- `Value`
- `ScheduledPage`

Veremos cada uno de estos modelos con más detalles en las siguientes secciones.

#### Site

Es donde almacenamos la información de cada *site* o *web* que queramos analizar. A la hora de crear un `Site`, tenemos que asignarle un nombre y una *url* de inicio. Todos los urls que casen con la url se consideran **enlaces internos** y se analizarán. Los que no, se consideran **enlaces externos** y se ignoran.

Por ejemplo, si nuestro Site define como pagina de inicio `http://localhost/alpha/`, entonces la página `http://localhost/alpha/algo/` se considera interna, pero `http://localhost/omega/` se considera externa y, por tanto, no se analizará. En otras palabras, se restrea `http://localhost/alpha/*`.

#### Page

Para cada url encontrada (Ya sea un enlace a otra url, una referencia a una imagen, a una hota de estilos css, etc.), si se considera interna, se creara una entrada en esta tabla.

Los campos de este modelo son:

- `id_page`: Clave primaria de la página.

- `site`: Clave foranea al modelo `Site`. Todas las páginas están vinculadas con un site,

- `subpath`: Concatentnado este campo con el campo `path` del _site_, obtenemos la ruta absoluta de la página. Si concatenamos `site.scheme` + `site.netloc` + `site.path` + `page.subpath` obtennos la URL absolute de la página (Ver método `page.url()`. 

- `params`: Si la URL incluye parámetros, se almacenan en este campo, en formato [JSON](https://es.wikipedia.org/wiki/JSON). Si no tiene parámetros, el valor será la cadena vacía, nunca `NULL`.
