#!/usr/bin/env python3

import os
import re
import traceback

from pathlib import Path
from typing import List

import operations.compile as compile
import operations.test as test

from core.task import Task
from input_parser import add_task
from utils.ui.tasks.check import CheckUI
from operations.simple.genpolls import GenPolls
from operations.simple.checkout import Checkout


class Sanity(Task):
    def __init__(self, timeout: int, genpolls: bool, persistent: bool, suppress_assertion: bool, count: int,
                 keep: bool = False, strict: bool = False, lookup: int = None, povs: bool = False,
                 coverage: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.current = None
        self.working_dir = None
        self.genpolls = genpolls
        self.suppress_assertion = suppress_assertion
        self.persistent = persistent
        self.count = count
        self.strict = strict
        self.lookup = lookup
        self.timeout = timeout
        self.ui = CheckUI()
        self.keep = keep
        self.povs = povs
        self.coverage = coverage

    def __call__(self):
        if not self.challenges:
            self.challenges = self.get_challenges()
            self.challenges.sort()

        self.lib_paths = self.kernel.get_lib_paths()

        try:
            for challenge in self.challenges:
                self.current = challenge
                self.ui(challenge)
                self.working_dir = f"/tmp/check_{self.current}"
                self.log_file = Path(self.working_dir, "check.log")
                if self.genpolls and self.lookup:
                    self._lookup()
                else:
                    self.check()
                os.system('clear')
                self.ui.print()
        except Exception as e:
            if not self.keep:
                self.dispose()
            self.log_file = Path("check_exception.log")
            self.status(f"The follwoing exception was raised for the challenge {self.current}")
            self.status(traceback.format_exc(), err=True)

    def dispose(self):
        os.system(f"rm -rf {self.working_dir}")
        self.log_file = None
        self.status("Deleted temporary files generated", bold=True)
        # os.system('clear')

    def check(self):
        operations = [self.check_checkout, self.check_compile, self.check_test]

        if self.genpolls:
            operations.insert(0, self.check_genpolls)

        for operation in operations:
            if not operation():
                self.ui.failed()
                break
            self.ui.header()
        else:
            self.ui.passed()

        if not self.keep:
            self.dispose()

    def _lookup(self):
        operations = [self.check_genpolls, self.check_checkout, self.check_compile, self.check_test]
        init = True
        pass_tests = False
        lookup = self.lookup

        for n in range(self.lookup):
            self.ui.lookup(n+1)
            for operation in operations:
                if not operation():
                    break
                if init:
                    init = False
                    operations = [self.check_genpolls, self.check_test]
                self.ui.header()
            else:
                self.ui.passed()
                pass_tests = True

            if pass_tests:
                self.lookup = None
                break
            elif n+1 == lookup:
                self.ui.failed()
            elif n+1 == (lookup-1):
                self.lookup = None

        self.lookup = lookup

        if not self.keep:
            self.dispose()

    def check_genpolls(self):
        genpolls = GenPolls(name="genpolls", kernel=self.kernel, challenge=self.current, count=self.count)
        out, err = genpolls()

        if err:
            if self.suppress_assertion and 'AssertionError' in err:
                self.ui.warn(operation="Genpolls", msg=err)
                return True
            self.ui.fail(operation="Genpolls", msg=err)

            if self.persistent:
                if not (self.lookup and self.genpolls):
                    self.kernel.exclude_challenge(challenge=self.current, msg="generating polls failed")

            return False

        self.ui.ok(operation="Genpolls", msg=f"(generated {genpolls.count} polls)")
        return True

    def check_checkout(self):
        checkout_cmd = Checkout(name="checkout", kernel=self.kernel, working_directory=self.working_dir,
                                challenge=self.current, sanity_check=True)
        out, err = checkout_cmd()

        if err:
            self.ui.fail(operation="Checkout", msg=err)
            return False

        self.ui.ok(operation="Checkout")
        return True

    def check_compile(self):
        compile_cmd = compile.Compile(name="compile", kernel=self.kernel, working_directory=self.working_dir,
                                      challenge=self.current, inst_files=None, fix_files=None, exit_err=False,
                                      log_file=self.log_file, sanity_check=True, coverage=self.coverage,
                                      gcc=self.coverage)
        compile_cmd.verbose = True
        out, err = compile_cmd()

        if err:
            self.ui.fail(operation="Compile", msg=err)

            return False

        self.ui.ok(operation="Compile")
        return True

    def check_test(self):
        self.status(f"Testing with timeout {self.timeout}.")
        if self.povs:
            test_cmd = test.Test(name="test", kernel=self.kernel, working_directory=self.working_dir, update=self.persistent,
                                 challenge=self.current, timeout=self.timeout, log_file=self.log_file, neg_pov=True,
                                 exit_fail=self.strict, neg_tests=True)
        else:
            test_cmd = test.Test(name="test", kernel=self.kernel, working_directory=self.working_dir, update=self.persistent,
                                 challenge=self.current, timeout=self.timeout, log_file=self.log_file, neg_pov=True,
                                 exit_fail=self.strict)

        test_outcome = test_cmd(save=True, stop=self.strict)
        neg_fails, pos_fails, passing, fails = [], [], [], []
        log_dict = {self.current: {}}

        for test_name, test_result in test_outcome.items():
            self.log(f"{self.current} {test_name};")
            if test_result.passed == 0 or test_result.code != 0:
                fails.append(f"{test_name} {test_result.passed}")

                if test_result.is_pov:
                    neg_fails.append(test_name)
                    log_dict[self.current][test_name] = {}

                    if test_result.not_ok:
                        log_dict[self.current][test_name]['msg'] = test_result.not_ok
                    else:
                        gcov_files = self.apply_gcov(test_cmd.build)
                        log_dict[self.current][test_name]['gcov'] = self.get_executed_lines(gcov_files)
                else:
                    pos_fails.append(test_name)
            else:
                passing.append(f"{test_name} {test_result.passed}")

        if not test_outcome or fails:
            self.ui.fail(operation="Test", msg=fails)
            self.ui.ok(operation="Test", msg=passing)

            if self.persistent and not (self.lookup and self.genpolls):
                msg = f"POVs {neg_fails} not working properly" if neg_fails else f"Polls {pos_fails} not working properly"
                self.kernel.exclude_challenge(challenge=self.current, msg=msg)

            return False

        if not test_cmd.challenge.paths.get_povs():
            test_cmd.challenge.paths.povs.mkdir(parents=True)
            super().__call__(cmd_str=f"cp {test_cmd.build}/*.pov {test_cmd.challenge.paths.povs}", msg=f"Saving povs.\n")

        self.ui.ok(operation="Test")
        return True

    def apply_gcov(self, build_path: Path):
        gcda_files = [p for p in build_path.rglob("*.gcda")]
        gcov_files = []

        for f in gcda_files:
            gcov_file = Path(f.parent, f.stem + '.gcov')
            super().__call__(cmd_str=f"gcov {f}", cmd_cwd=str(f.parent),
                             msg=f"Generating coverage file for {f}\n", exit_err=False)
            if gcov_file.exists():
                gcov_files.append(gcov_file)
            f.unlink()

        return gcov_files

    def get_executed_lines(self, gcov_files: List[Path]):
        executed_line_pattern = "^\s+(\d+):\s+(\d+):\s*(.*)\n"
        gcovs_executed_lines = {}

        for gcov_file in gcov_files:
            executed_lines = []
            with gcov_file.open(mode="r") as gf:
                for line in gf.readlines():
                    match = re.search(executed_line_pattern, line)
                    if match:
                        executed_lines.append(match.groups())
            if executed_lines:
                gcovs_executed_lines[gcov_file.stem] = executed_lines
            gcov_file.unlink()

        return gcovs_executed_lines

    def __str__(self):
        check_cmd_str = " --challenges " + ' '.join(self.challenges)
        check_cmd_str += f" --timeout {self.timeout}"
        check_cmd_str += f" --count {self.count}"

        if self.persistent:
            check_cmd_str += f" --persistent"

        if self.genpolls:
            check_cmd_str += f" --genpolls"

        return super().__str__() + check_cmd_str + "\n"


def check_args(input_parser):
    input_parser.add_argument('--timeout', type=int, default=60, help='The timeout for tests in seconds.')
    input_parser.add_argument('--count', type=int, default=10, help='Number of polls to generate.')
    input_parser.add_argument('--genpolls', action='store_true', help='Flag for enabling polls generation.')
    input_parser.add_argument('--lookup', type=int, default=None, help='Useful for generating polls that pass.')
    input_parser.add_argument('--keep', action='store_true', help='Keeps the files generated.')
    input_parser.add_argument('--povs', action='store_true', help='Tests only POVs.')
    input_parser.add_argument('--coverage', action='store_true', help='Enables coverage (for profiling and debugging).')
    input_parser.add_argument('-sa', '--suppress_assertion', action='store_true',
                              help='Flag for suppressing assertion errors during polls generation.')
    input_parser.add_argument('--strict', action='store_true', help='Stops testing at the first fail.')
    input_parser.add_argument('--persistent', action='store_true',
                              help="Flag for excluding challenges that fail and persist results in the metadata.")


info_parser = add_task("sanity", Sanity, description="Sanity checks for challenges.")
check_args(info_parser)
