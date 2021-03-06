#!/usr/bin/env python3
import json
from dataclasses import dataclass
from os.path import dirname, abspath
from pathlib import Path

from utils.paths import LibPaths, Tools

ROOT_DIR = dirname(dirname(__file__))
SOURCE_DIR = dirname(abspath(__file__))


@dataclass
class Configuration:
    root: Path
    src: Path
    lib_paths: LibPaths
    tools: Tools
    plots: Path
    metadata: Path
    tests_timeout: str  # In seconds
    margin: int     # In seconds
    cores: Path
    python2: str

    def validate(self):
        return self.src.exists() and self.plots.exists() and self.lib_paths.validate() and self.metadata.exists() \
               and self.tools.validate() and int(self.tests_timeout) > 0 and int(self.margin) > 0 and self.cores.exists()


lib_path = Path(ROOT_DIR) / Path("lib")
tools_path = Path(ROOT_DIR) / Path("tools")
metadata = lib_path / Path("metadata")
lib_paths = LibPaths(root=lib_path,
                     polls=lib_path / Path("polls"),
                     povs=lib_path / Path("povs"),
                     challenges=lib_path / Path("challenges"))

tools = Tools(root=tools_path,
              cmake_file=tools_path / Path("CMakeLists.txt"),
              cmake_file_no_patch=tools_path / Path("CMakeListsNoPatch.txt"),
              compile=tools_path / Path("compile.sh"),
              test=tools_path / Path("cb-test.py"),
              gen_polls=tools_path / Path("generate-polls", "generate-polls"),
              scores=tools_path / Path('cwe_scores.pkl'))

configuration = Configuration(root=Path(ROOT_DIR),
                              src=Path(ROOT_DIR) / Path(SOURCE_DIR),
                              lib_paths=lib_paths,
                              tools=tools,
                              plots=Path(ROOT_DIR) / Path('plots'),
                              metadata=metadata,
                              tests_timeout="60",
                              margin=5,
                              cores=Path("/cores"),
                              python2="python")
