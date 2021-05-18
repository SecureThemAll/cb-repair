#!/usr/bin/env python3

from core.operation import Operation
from input_parser import add_operation


class Info(Operation):
    def __init__(self, kind: str, **kwargs):
        super().__init__(**kwargs)
        self.kind = kind

    def __call__(self):
        if self.kind == "prefix":
            self._set_build_paths()

            print(self.cmake)

        elif self.kind == "count_tests":
            self._set_build_paths()
            self.challenge.load_pos_tests()
            neg_tests = [pd for pd in self.source.iterdir() if pd.match("pov*") and pd.is_dir()]

            print(f"{len(self.challenge.pos_tests)} {len(neg_tests)} ")
        else:
            print(self.challenge.info())
            return self.challenge.info()


def info_args(input_parser):
    input_parser.add_argument('--kind', help='Info kind to be displayed.',
                              choices=["prefix", "count_tests"], type=str, default=None)


info_parser = add_operation("info", Info, 'Query information about the benchmark challenges.')
info_args(info_parser)
