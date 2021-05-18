#!/usr/bin/env python3
import subprocess
import psutil

from os import environ
from sys import stderr
from typing import Union, AnyStr, Tuple, List
from pathlib import Path
from threading import Timer

from .kernel import Kernel
from utils.ui.terminal import TermPrint


class Command:
    def __init__(self, name: str, kernel: Kernel, log_file: str = None, verbose: bool = False,
                 no_status: bool = False, **kwargs):
        self.name = name
        self.return_code = 0
        self.kernel = kernel
        self.env = environ
        self.no_status = no_status
        self.log_file = Path(log_file) if log_file else log_file
        self.verbose = verbose
        self.output, self.error = None, None

        if kwargs:
            self.log(f"Unknown arguments: {kwargs}\n")

    def set_env(self):
        self.env = environ.copy()

    def _exec(self, proc: subprocess.Popen):
        out = []

        for line in proc.stdout:
            decoded = line.decode()
            out.append(decoded)

            if self.verbose:
                print(decoded, end='')

            self.log(decoded)

        self.output = ''.join(out)

        proc.wait(timeout=1)

        if proc.returncode and proc.returncode != 0:
            self.return_code = proc.returncode
            proc.kill()
            self.error = proc.stderr.read().decode()
            
            if not self.error:
                self.error = f"Return code: {proc.returncode}"

            if self.verbose:
                print(self.error, file=stderr)

            self.log(self.error)

    def __call__(self, cmd_str: Union[AnyStr, List[AnyStr]], cmd_cwd: str = None, msg: str = None,
                 timeout: int = None, exit_err: bool = False) -> Tuple[Union[str, None], Union[str, None]]:

        if msg:
            if not self.no_status:
                print(msg)
            if self.verbose:
                print(cmd_str)

        self.log(msg)
        self.log(f"Command: {cmd_str}\n")

        # based on https://stackoverflow.com/a/28319191
        with subprocess.Popen(args=cmd_str,
                              shell=isinstance(cmd_str, str),
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              env=self.env,
                              cwd=cmd_cwd) as proc:
            if timeout:
                timer = Timer(timeout, _timer_out, args=[proc, self])
                timer.start()
                self._exec(proc)
                proc.stdout.close()
                timer.cancel()
            else:
                self._exec(proc)

            if exit_err and self.error:
                exit(proc.returncode)

            return self.output, self.error

    def status(self, message: str, err: bool = False, bold: bool = False, ok: bool = False, warn: bool = False,
               nan: bool = False):
        self.log(message)

        if self.no_status:
            return

        if ok:
            TermPrint.print_pass(message)
        elif err:
            TermPrint.print_fail(message)
        elif bold:
            TermPrint.print_bold(message)
        elif warn:
            TermPrint.print_warn(message)
        elif nan:
            print(message)
        else:
            TermPrint.print_info(message)

    def log(self, msg: str):
        if self.log_file and msg:
            with self.log_file.open(mode="a") as lf:
                lf.write(msg)

    def __str__(self):
        cmd_str = f"{self.name}"

        if self.verbose:
            cmd_str += " -v"
        if self.no_status:
            cmd_str += " -ns"
        if self.log_file:
            cmd_str += f" -l {self.log_file}"
        if self.kernel.excl:
            cmd_str += " -excl"

        return cmd_str


# https://stackoverflow.com/a/54775443
def _timer_out(p: subprocess.Popen, cmd: Command):
    print("Command timed out")
    process = psutil.Process(p.pid)
    cmd.return_code = p.returncode if p.returncode else -3

    for proc in process.children(recursive=True):
        proc.kill()

    process.kill()
