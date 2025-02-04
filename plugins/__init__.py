#!/usr/bin/env python3

from os.path import dirname
from pathlib import Path
import importlib

BASE_PATH = Path(dirname(__file__))


class PluginRegistry:

    def __init__(self):
        self.modules = {
            f.stem: None
            for f in BASE_PATH.glob('*.py')
            if not f.stem.startswith('_')
            }
        self._initialized = False

    def initialize(self):
        if not self._initialized:
            for module_name in self.modules:
                _module = importlib.import_module(f'spidercheck.plugins.{module_name}')
                _process = getattr(_module, 'process')
                self.modules[module_name] = _process
            self._initialized = True

    def get_all_plugins(self):
        if not self._initialized:
            self.initialize()
        for name in self.modules:
            yield name, self.modules[name]


registry = PluginRegistry()
