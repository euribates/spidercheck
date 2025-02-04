Procesos en Spidercheck
------------------------------------------------------------------------


Comprobación de una página
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

El proceso más importante que realiza Spidercheck es la comprobación de
una página. El código está en ``core.check_page(page)``. A partir de una
instancia de la página, se realizan los siguientes pasos:

- Marca la página como que se ha intentado comprobar (Pone los campos
  checked_at a la fecha y hora actual, se marca el campo ``is_checked``
  como verdadero.

- Intenta obtener las cabeceras de respuesta de la página (Una petición
  ``HEAD``). Si se produce un error, se almacena la información del
  error, y se para el proceso.

- Si todo ha ido bien, se comprueba si la página es HTML, y si es
  una página interna. En ese caso, se realiza una
  petición `GET` para obtener tanto las cabeceras como el contenido de
  la página. Tanto las cabeceras como el cuerpo de la páginas se pasan
  a todos los *plugins* del sistema. Los valores devueltos, si los
  hubiera, siempre han de ser un diccionario de valores. Esos valores se
  almacenan en el modelo `Value`, vinculados a la página.


Inicialización de un *Site*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A partir de un nombre y una *url* semilla, la función para crear un
nuevo site está en ``core.init_site``.

.. autofunction:: .core::init_size
