import random

from pycluster.messenger.helpers import math

from toonbattle.calculator.common.avatar import AvatarHolder, Cog, Toon
from toonbattle.calculator.helpers.decorators import check_subject
from toonbattle.calculator.helpers.enums import AuxillaryObjects, ClashEffects, MathTargets
from toonbattle.calculator.globals import ClashObjectRegistry as COReg
from toonbattle.calculator.common.status_effects import StatusEffectController

COReg.bind(AuxillaryObjects.AvatarHolder, AvatarHolder)
COReg.bind(AuxillaryObjects.StatusEffectController, StatusEffectController)
COReg.bind(AuxillaryObjects.Toon, Toon)


@COReg.register(AuxillaryObjects.Cog)
class ClashCog(Cog):
    executive: bool = False

    @classmethod
    def from_level(
        cls,
        holder: AvatarHolder,
        level: int,
        exe: bool = False,
        skelecog: int = 0,
        attack_oriented: bool | None = None,
        **kwargs
    ) -> "ClashCog":
        max_health = (level + 1) * (level + 2)

        defense = min(max((level - 1) * 0.05, 0.02), 0.65)
        if attack_oriented is True:
            defense -= 0.1
            max_health = (level + 2) * (level + 3) - 2
        elif attack_oriented is False:
            defense += 0.1
            max_health = level * (level + 1) + 1

        if exe:
            defense += 0.05
            max_health *= 1.5

        if skelecog:
            max_health *= 1.1 - (random.random() * 0.2 * skelecog)

        cog = holder.create(max_health=max_health, defense=defense, cast_to=ClashCog)
        cog.executive = exe
        if skelecog:
            cog.parent_cluster.create_effect(cog, ClashEffects.SkelecogReduction, stacks=skelecog)
        return cog

    @property
    def manager(self) -> bool:
        return self.health / self.max_health >= 1.5

    @math(MathTargets.EffectRounds, priority=-100)
    @check_subject
    def change_effect_rounds(self, value: int, **kwargs):
        if self.manager:
            return 2
        return value
