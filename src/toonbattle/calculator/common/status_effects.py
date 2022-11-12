import typing

from pycluster.messenger.helpers import listen

from toonbattle.calculator.helpers.enums import Events, MathTargets
from toonbattle.calculator.globals import CalculationObject

if typing.TYPE_CHECKING:
    from toonbattle.calculator.common.avatar import Avatar
    from toonbattle.calculator.common.state import CalculationState


class StatusEffectController(CalculationObject):
    parent: "Avatar"

    @property
    def registry(self):
        return self.parent_cluster.StatusEffectRegistry

    def remove(self, effect: "StatusEffect"):
        effect.cleanup()
        self.remove_child(str(effect.object_type))

    def __len__(self):
        return len(self.children)

    def __repr__(self):
        return f"StatusEffects{list(self.children.keys())}"

    def add_child(self, child_id: str, child: "StatusEffect", allow_subtrees: bool = False) -> "StatusEffect":
        return typing.cast("StatusEffect", super().add_child(child_id, child, True))

    def get(self, effect_id) -> "StatusEffect":
        return typing.cast("StatusEffect", super().get(str(effect_id)))

    def __getitem__(self, item) -> "StatusEffect":
        return typing.cast("StatusEffect", super().__getitem__(str(item)))


class StatusEffect(CalculationObject):
    parent: StatusEffectController

    @property
    def parent_avatar(self) -> "Avatar":
        return self.parent.parent

    @listen(Events.ToonsMoved)
    def first_cleanup(self):
        pass

    @property
    def parent_cluster(self) -> "StatusEffectController":
        return self.parent

    @property
    def true_parent_cluster(self) -> "CalculationState":
        return typing.cast("CalculationState", self.parent.parent_cluster)

    def update(self, **kwargs):
        pass


class StatusEffectTimed(StatusEffect):
    turns: int
    DefaultTurns: int = 3

    def __init__(self, parent, turns: int = None, **kwargs):
        super().__init__(parent, **kwargs)

        if turns is None:
            turns = self.DefaultTurns

        turns = self.calculate(MathTargets.EffectRounds, turns, subject=self.parent_avatar, effect=self)
        self.turns = max(1, int(turns))

    @listen(Events.ToonsMoved)
    def first_cleanup(self):
        self.turns -= 1
        if self.turns <= 0:
            self.parent.remove(self)
        super().first_cleanup()

    @property
    def datagram(self):
        return self.turns

    @datagram.setter
    def datagram(self, value):
        self.turns = value
