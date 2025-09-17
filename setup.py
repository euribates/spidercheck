from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name='Spidercheck',
    description="Web server check spider",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version='0.6',
    license='MIT NON-AI',
    author="Juan Ignacio Rodríguez de León",
    author_email='euribates@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/euribates/spidercheck',
    keywords='web spider django check quality',
    install_requires=[
      ],

)
