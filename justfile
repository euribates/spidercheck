set dotenv-load := true

# Realiza un chequeo previo de Django
check: clean
    python3 ./manage.py check
    python3 ./manage.py validate_templates

# Mostrar información del Sistema operativo / Hardware / Python / Django
info:
    @echo "OS: {{os()}} / {{os_family()}}"
    @echo "This is an {{arch()}} machine"
    python3 -V
    python3 -c "import django; print(django.__version__)"
    uptime

# static: Genera contenidos estáticos
static:
    python3 manage.py collectstatic --no-input

# Abre una shell python con el entorno de Django cargado
shell:
    python3 ./manage.py shell_plus

# Ejecutar batería de test lentos (Empezará por el último que haya fallado)
test_slow *args='.':
    python3 -m pytest --failed-first -vv -x --log-cli-level=INFO --doctest-modules -m "slow" {{ args }}

# Ejecutar los test pasados como paræmetro (Empezará por el último que haya fallado)
test *args='.':
    python3 -m pytest --failed-first -vv -x --log-cli-level=INFO --doctest-modules -m "not slow" {{ args }}

# Ejecuta solo los tests marcados con wip (Work in Progress)
test_wip *args='.':
    python3 -m pytest --failed-first -vv -x --log-cli-level=INFO -m wip {{ args }}

# Genera el fichero de tags
tags: clean
    cd {{justfile_directory()}} && ctags -R --exclude=*.js .

# Borra todos los ficheros compilados python (*.pyc, *.pyo, __pycache__)
clean:
    sudo find . -type d -name "__pycache__" -exec rm -r "{}" +
    sudo find . -type d -name ".mypy_cache" -exec rm -r "{}" +
    sudo find . -type d -name ".pytest_cache" -exec rm -r "{}" +
    sudo find . -type f -name "*.pyc" -delete
    sudo find . -type f -name "*.pyo" -delete
    if [ -e .ruff_cache ]; then rm -r .ruff_cache/; fi


# Alias para usar spidercheck
sc *args='':
    python3 ./manage.py spidercheck  {{ args }}

# Acceso al DBShell
dbshell *args='default':
    python3 manage.py dbshell --database {{ args }}

# Generar la documentación con Sphinx
docs: clean
    sphinx-build -W -c docs/ -b html . ./html
