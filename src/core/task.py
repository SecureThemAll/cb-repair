#!/usr/bin/env python3
from typing import List, AnyStr

from .command import Command


class Task(Command):
    def __init__(self, challenges: List[AnyStr], **kwargs):
        super().__init__(**kwargs)
    
        if challenges:
            for challenge in challenges:
                self.kernel.has_challenge(challenge)
                if not self.kernel.excl:
                    self.kernel.is_excluded(challenge)

            self.challenges = challenges
            self.challenges.sort()
        else:
            self.challenges = self.kernel.challenges.copy()

    def __str__(self):
        return super().__str__()
