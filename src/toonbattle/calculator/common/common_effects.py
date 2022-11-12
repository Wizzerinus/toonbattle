from pycluster.messenger.helpers import math

from toonbattle.calculator.common.status_effects import StatusEffectTimed
from toonbattle.calculator.helpers.decorators import check_subject
from toonbattle.calculator.helpers.enums import MathTargets


class EffectStun(StatusEffectTimed):
    DefaultTurns = 1

    def __init__(self, parent, stacks=1, **kwargs):
        super().__init__(parent, **kwargs)
        self.stacks = stacks

    def update(self, stacks=1, **kwargs):
        self.stacks += stacks

    @property
    def datagram(self):
        return self.turns, self.stacks

    @datagram.setter
    def datagram(self, value):
        self.turns, self.stacks = value

    @math(MathTargets.Accuracy)
    @check_subject
    def calculate_accuracy(self, value: float, **kwargs):
        return value + 0.2 * self.stacks
