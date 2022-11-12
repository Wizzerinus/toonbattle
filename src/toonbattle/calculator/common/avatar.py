from typing import Optional, Type, TypeVar

from pycluster.messenger.helpers import math
from pycluster.util.action_lock import ActionLock

from toonbattle.calculator.helpers.decorators import check_subject
from toonbattle.calculator.helpers.enums import AuxillaryObjects, MathTargets
from toonbattle.calculator.globals import CalculationObject

from toonbattle.calculator.common.status_effects import StatusEffectController


class Avatar(CalculationObject):
    effects: StatusEffectController
    avatar_id: int
    health: int
    max_health: int

    def __init__(self, holder: "AvatarHolder", avatar_id: int = 0, max_health: float = 0, **kwargs):
        super().__init__(holder, **kwargs)
        self.effects = self.registry.create_and_insert(AuxillaryObjects.StatusEffectController, self, "effects")
        self.avatar_id = avatar_id
        self.health = self.max_health = int(max_health)

    @property
    def datagram(self):
        return self.avatar_id, self.health, self.max_health

    @datagram.setter
    def datagram(self, value):
        self.avatar_id, self.health, self.max_health = value

    def __repr__(self):
        return f"{self.__class__.__name__}({self.health}/{self.max_health})"


T = TypeVar("T", bound=Avatar)


class Cog(Avatar):
    def __init__(self, holder: "AvatarHolder", avatar_id: int = 0, max_health: float = 0, defense: int = 0, **kwargs):
        super().__init__(holder, avatar_id, max_health, **kwargs)
        self.defense = defense

    @property
    def datagram(self):
        return self.avatar_id, self.health, self.max_health, self.defense

    @datagram.setter
    def datagram(self, value):
        self.avatar_id, self.health, self.max_health, self.defense = value

    @math(MathTargets.Accuracy)
    @check_subject
    def calculate_accuracy(self, value: float, **kwargs):
        return value - self.defense

    @classmethod
    def from_level(cls, holder: "AvatarHolder", level: int, **kwargs):
        max_health = (level + 1) * (level + 2)
        defense = min(max((level - 1) * 0.05, 0.02), 0.55)
        return holder.create(max_health=max_health, defense=defense)


class Toon(Avatar):
    pass


class AvatarHolder(CalculationObject):
    children: dict[str, Avatar]

    def __init__(self, parent, subclass_id: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.subclass_id = subclass_id
        self.avatar_order = []
        self.avatar_lock = ActionLock()

    def create(self, cast_to: Type[T] = Avatar, **kwargs) -> T:
        avatar_id = self.parent_cluster.allocate()
        avatar = self.registry.create_and_insert(
            self.subclass_id, self, avatar_id, avatar_id=avatar_id, **kwargs, cast_to=cast_to
        )
        return avatar

    def remove(self, avatar: Avatar) -> None:
        if avatar.avatar_id in self.avatar_order:
            self.avatar_order.remove(avatar.avatar_id)
        avatar.cleanup()
        with self.avatar_lock as lock:
            lock.delitem(self.children, str(avatar.avatar_id))

    def remove_dead_avatars(self) -> None:
        with self.avatar_lock:
            for avatar in self.children.values():
                if avatar.health <= 0:
                    self.remove(avatar)

    def __getitem__(self, item: int) -> Avatar:
        item = int(item)
        if item > 90:
            return self.children[str(item)]
        return self.children[self.avatar_order[item]]

    def __call__(self, item: int) -> Optional[Avatar]:
        try:
            item = int(item)
        except (TypeError, ValueError):
            return None

        if item > 90:
            return self.children.get(str(item))
        if item >= len(self.avatar_order) or item < 0:
            return None
        return self.children.get(self.avatar_order[item], None)

    def __repr__(self):
        dumped_children = []
        for i in self.avatar_order:
            if i in self.children:
                dumped_children.append(repr(self.children[i]))
            else:
                dumped_children.append("?")
        return f"AvatarHolder({self.subclass_id})[{', '.join(dumped_children)}]"

    def __len__(self):
        return len(self.avatar_order)

    def __iter__(self):
        return (self[i] for i in range(len(self.avatar_order)))

    @property
    def datagram(self):
        return self.avatar_order

    @datagram.setter
    def datagram(self, avatar_order: list[int]):
        self.avatar_order = avatar_order

    def add_child(self, child_id: str, child: Avatar, allow_subtrees: bool = False):
        super().add_child(child_id, child, allow_subtrees)
        if child_id not in self.avatar_order:
            self.avatar_order.append(child_id)

    def index(self, av: Avatar) -> int:
        try:
            return self.avatar_order.index(av.avatar_id)
        except ValueError:
            return -1
