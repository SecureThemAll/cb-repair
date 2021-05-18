#!/usr/bin/env python3
import json
from typing import AnyStr

from filelock import FileLock

from config import Configuration
from utils.challenge import Challenge
from utils.ui.terminal import TermPrint


class Kernel:
    def __init__(self,
                 configs: Configuration,
                 excl: bool = False,
                 **kwargs):
        self.configs = configs
        self.excl = excl

        if not self.configs.metadata.exists():
            TermPrint.print_warn(f"Not initialized: run ./init.py")
            exit(1)

        self.global_metadata = {}
        self.load_metadata()
        self.challenges = [challenge for challenge, metadata in self.global_metadata.items() if
                           not (metadata["excluded"] and not excl)]
        self.challenges.sort()

    def has_challenge(self, challenge_name: str, fail: bool = True):
        if challenge_name not in self.global_metadata:
            TermPrint.print_fail(f"No {challenge_name} challenge")
            if fail:
                exit(1)
            return False
        return True

    def is_excluded(self, challenge_name: str, force_exit: bool = True):
        if self.global_metadata[challenge_name]['excluded']:
            if not self.excl:
                TermPrint.print_warn(f"Challenge {challenge_name} was excluded.")

                if force_exit:
                    exit(1)

                return False

            return True

    def get_challenge(self, challenge_name: str):
        # Check if challenge is valid
        self.has_challenge(challenge_name)
        self.is_excluded(challenge_name)
        # Generate Paths
        paths = self.get_challenge_paths(challenge_name)

        return Challenge(paths, metadata=self.global_metadata[challenge_name])

    def exclude_challenge(self, challenge: AnyStr, msg: AnyStr):
        self.load_metadata()
        self.global_metadata[challenge]["excluded"] = True
        self.save_metadata()
        TermPrint.print_warn(f"Challenge {challenge} excluded: {msg}")

    def get_challenge_paths(self, challenge_name: str):
        return self.configs.lib_paths.get_challenge_paths(challenge_name)

    def get_lib_paths(self):
        return self.configs.lib_paths

    def get_tools(self):
        return self.configs.tools

    def has_sanity(self, challenge_name: AnyStr):
        return self.global_metadata[challenge_name]['sanity'] != {}

    def get_sanity(self, challenge_name: AnyStr):
        return self.global_metadata[challenge_name]['sanity']

    def reset_sanity(self, challenge_name: AnyStr):
        self.global_metadata[challenge_name]['sanity'] = {}

    def get_test_duration(self, challenge_name: AnyStr, test_name: AnyStr, is_pov: bool):
        challenge_metadata = self.global_metadata[challenge_name]['sanity']

        if test_name in challenge_metadata:
            if is_pov:
                return max([outcome['duration'] for _, outcome in challenge_metadata.items() if 'duration' in outcome])*2
            return challenge_metadata[test_name]['duration']

        return None

    def update_sanity(self, challenge_name: str, test_name: str, outcome: int, duration: int, code: int = None,
                      signal: int = None):
        challenge_metadata = self.global_metadata[challenge_name]['sanity']

        challenge_metadata[test_name] = {
            'outcome': outcome,
            'duration': duration
        }

        if code:
            challenge_metadata[test_name]['error'] = code

        if signal:
            challenge_metadata[test_name]['signal'] = signal

        self.save_metadata()
        # self.global_metadata[self.challenge.name]['sanity'] = challenge_metadata

    def include_challenge(self, challenge_name: str):
        self.global_metadata[challenge_name]['excluded'] = False
        self.save_metadata()
        TermPrint.print_info(f"Challenge {challenge_name} included.")

    def load_metadata(self):
        with self.configs.metadata.open(mode="r") as m:
            self.global_metadata = json.load(m)

    def save_metadata(self, new_metadata: dict = None):
        lock = FileLock(str(self.configs.metadata) + '.lock')

        with lock:
            with self.configs.metadata.open(mode="w") as m:
                json.dump(new_metadata if new_metadata else self.global_metadata, m, indent=2)
