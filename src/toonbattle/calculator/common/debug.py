from pycluster.messenger.helpers import replace

from toonbattle.calculator.common.status_effects import StatusEffect
from toonbattle.calculator.helpers.enums import ReplaceTargets


class GagsAlwaysHit(StatusEffect):
    @replace(ReplaceTargets.GagAccuracy)
    def recalculate_accuracy(self, *args, **kwargs):
        return 1
