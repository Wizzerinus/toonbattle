import abc
import logging
import random
from typing import Sequence, TYPE_CHECKING, cast

from pycluster.messenger.helpers import replaceable

from toonbattle.calculator.common.avatar import Avatar
from toonbattle.calculator.globals import CalculationObject
from toonbattle.calculator.helpers.enums import MathTargets, ReplaceTargets

if TYPE_CHECKING:
    from toonbattle.calculator.common.state import CalculationState


class Attack(CalculationObject, abc.ABC):
    logger = logging.getLogger("toonbattle.calculator.Attack")

    @abc.abstractmethod
    def get_accuracy(self, other_self: "Attack") -> float:
        # other_self is a hack to make this work with the @replaceable decorator
        pass

    @property
    def hit(self):
        return self.get_accuracy(self) >= random.random()

    @property
    def true_parent_cluster(self) -> "CalculationState":
        return cast("CalculationState", self.parent.parent_cluster)

    @property
    @abc.abstractmethod
    def priority(self) -> float:
        pass


class GagPart:
    level: int
    author: Avatar
    target: tuple[Avatar, ...]

    def __repr__(self):
        return f"({self.level} <- {self.author}({self.author.avatar_id}))"


class TrackConfiguration:
    accuracy: tuple[float, ...]
    damages: tuple[int, ...]

    def __init__(self, accuracy: float | Sequence[float], damages: Sequence[int], **kwargs):
        self.accuracy = tuple(accuracy) if not isinstance(accuracy, float) else (accuracy,) * len(damages)
        self.damages = tuple(damages)
        self.extras = kwargs


class GagDefinition(Attack):
    track: int
    gag_parts: list[GagPart]
    configuration: dict[int, TrackConfiguration]
    target: tuple[Avatar, ...]
    targets_toons: bool = False

    def construct(self, track: int, target: int | tuple, gag_parts: Sequence[GagPart]):
        self.track = track

        av_list = self.true_parent_cluster.cogs if not self.targets_toons else self.true_parent_cluster.toons

        target_cog = av_list(target)
        if target_cog:
            self.target = (target_cog,)
        else:
            self.target = tuple(av_list)
        self.gag_parts = list(gag_parts)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.track}, {self.gag_parts})"

    @property
    def levels(self) -> tuple[int, ...]:
        return tuple(part.level for part in self.gag_parts)

    @property
    def max_level(self) -> int:
        return max(self.levels)

    @property
    def base_accuracy(self):
        return max(self.configuration[self.track].accuracy[x] for x in self.levels)

    @replaceable(ReplaceTargets.GagAccuracy)
    def get_accuracy(self, other_self):
        return min(
            self.calculate(MathTargets.Accuracy, 0.7 + self.base_accuracy, gags=self.gag_parts, subject=self.target),
            0.95,
        )

    @property
    def priority(self):
        state = self.true_parent_cluster
        authors = [x.author for x in self.gag_parts]
        author_indexes = [state.toons.index(x) for x in authors]
        if any(x == -1 for x in author_indexes):
            self.logger.warning(f"Authors of {self} not found in state.toons")
        return 100 * self.track + 10 * min(self.levels) + min(author_indexes)

    def apply(self) -> bool:
        if self.hit:
            self.apply_hit()
            return True
        else:
            self.apply_miss()
            return False

    def apply_hit(self):
        pass

    def apply_miss(self):
        pass


class GagController(CalculationObject):
    parent: "CalculationState"

    @property
    def registry(self):
        return self.parent_cluster.GagRegistry

    def __len__(self):
        return len(self.children)

    def add_child(self, child_id: str, child: GagDefinition, allow_subtrees: bool = False) -> "GagDefinition":
        return cast(GagDefinition, super().add_child(child_id, child, True))
