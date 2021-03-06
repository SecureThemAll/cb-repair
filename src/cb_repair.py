#!/usr/bin/env python3

from config import configuration
from input_parser import parser, run
from core.kernel import Kernel


if __name__ == "__main__":
    args, unk_args = parser.parse_known_args()
    vars_args = dict(vars(args))
    vars_args.update({"configs": configuration})
    vars_args.update({"unknown": unk_args})
    run(kernel=Kernel(**vars_args), **vars_args)
