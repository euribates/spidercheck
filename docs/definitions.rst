Definiciones e información general
------------------------------------------------------------------------

Un rastreador web comienza con una lista de direcciones URL para
visitar, llamado **semillas**. Como se comentó antes, Spidercheck,
aunque empieza con una semilla con una única dirección, durante el
proceso usa una lista de direcciones pendientes a rastrear, este
conjunto de direcciones se llama **frontera de rastreo**.

Spiderchek **no es una araña de restreo general**, sino que está
orientada a un único servidor web, o incluso a una sección de un
servidor web. Por ello, y para evitar que siga los enlaces externos que
podrían llevarle en a intentar rastrear tola la Internet, solo incluye
en la frontera de rastreo las URL que están definidas debajo de la
semilla inicial. Es decir, que si la semilla inicial empieza en
``http://uvw.es/``, entonces un enlace a, por ejemplo,
``http://uvw.es/about/`` se considera un **enlace interno** y se añade a
la frontera, pero un enlace a ``http://xyz.es/`` se considera
**externo** y, por tanto, no se incluye.
 
El gran volumen de páginas implica también que el rastreador sólo puede
descargar un número limitado de páginas en un tiempo determinado, por lo
que necesita dar algún tipo de prioridad a sus descargas. Además, como
las páginas pueden ser modificadas en el futuro, hay que tener en cuenta
que incluso una página recién comprobada tendrá que ser analizada de
nuevo en un futuro más o menos cercano.

