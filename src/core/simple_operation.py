#!/usr/bin/env python3

from .command import Command


class SimpleOperation(Command):
    def __init__(self,
                 challenge: str,
                 **kwargs):
        super().__init__(**kwargs)
        self.challenge = self.kernel.get_challenge(challenge_name=challenge)

    def __str__(self):
        return super().__str__() + f" -cn {self.challenge.name}"
