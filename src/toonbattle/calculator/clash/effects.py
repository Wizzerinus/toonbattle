from pycluster.messenger.helpers import listen, math, replace
from pycluster.messenger.message_object import FizzleReplace

from toonbattle.calculator.common.avatar import Avatar
from toonbattle.calculator.common.debug import GagsAlwaysHit
from toonbattle.calculator.helpers.decorators import check_object, check_source, check_subject
from toonbattle.calculator.helpers.enums import (
    ClashEffects,
    CommonEffects,
    DamageSources,
    Events,
    ExtraSources,
    MathTargets,
    ReplaceTargets,
)
from toonbattle.calculator.common.common_effects import EffectStun
from toonbattle.calculator.common.status_effects import StatusEffect, StatusEffectController, StatusEffectTimed
from toonbattle.calculator.globals import ClashEffectRegistry as CFReg

CFReg.bind(0, StatusEffectController)
CFReg.bind(CommonEffects.Stun, EffectStun)
CFReg.bind(CommonEffects.ToonsHit, GagsAlwaysHit)


@CFReg.register(ClashEffects.Cheer)
class EffectCheer(StatusEffectTimed):
    DefaultTurns = 1

    @math(MathTargets.Accuracy)
    @check_object
    def calculate_accuracy(self, value: float, **kwargs):
        return value + 0.2


@CFReg.register(ClashEffects.Trapped)
class EffectTrapped(StatusEffect):
    def __init__(self, parent, value: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.value = value

    @property
    def datagram(self):
        return self.value

    @datagram.setter
    def datagram(self, value):
        self.value = value

    @replace(ReplaceTargets.CreateEffect)
    def replace_lure_creation(self, avatar: Avatar, effect_id: int, **kwargs):
        if avatar is not self.parent_avatar or effect_id is not ClashEffects.Lured:
            return FizzleReplace

        self.parent.remove(self)
        state = self.true_parent_cluster
        state.deal_damage(self.parent_avatar, self.value)
        state.create_effect(self.parent_avatar, ClashEffects.Dazed, source=DamageSources.TrappedEffect)


@CFReg.register(ClashEffects.Dazed)
class EffectDazed(StatusEffectTimed):
    DefaultTurns = 2

    @math(MathTargets.Accuracy)
    @check_subject
    def calculate_accuracy(self, value: float, **kwargs):
        return value + 0.1


@CFReg.register(ClashEffects.Lured)
class EffectLured(StatusEffectTimed):
    def __init__(self, parent, knockback: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.knockback = knockback

    @property
    def datagram(self):
        return self.turns, self.knockback

    @datagram.setter
    def datagram(self, value):
        self.turns, self.knockback = value

    @math(MathTargets.Damage)
    @check_subject
    def replace_damage(self, value: float, source: int = None, extra_source: int = None, **kwargs):
        if source in (DamageSources.Squirt, DamageSources.Throw) and extra_source != ExtraSources.ComboDamage:
            return value + self.knockback
        return value

    @replace(ReplaceTargets.GagAccuracy)
    def replace_gag_accuracy(self, subject: Avatar, **kwargs):
        if subject is not self.parent_avatar:
            return FizzleReplace

        return 1.0

    @listen(Events.DamageDealt)
    @check_subject
    def dealt_damage(self, source: int = None, **kwargs):
        if source in (DamageSources.Squirt, DamageSources.Sound, DamageSources.Throw, DamageSources.Zap):
            self.parent.remove(self)


@CFReg.register(ClashEffects.Soak)
class EffectSoak(StatusEffectTimed):
    @math(MathTargets.Accuracy)
    @check_subject
    def calculate_accuracy(self, value: float, **kwargs):
        return value + 0.1


@CFReg.register(ClashEffects.Encore)
class EffectEncore(StatusEffectTimed):
    DefaultTurns = 2

    def __init__(self, parent, multiplier: float, **kwargs):
        super().__init__(parent, **kwargs)
        self.multiplier = multiplier

    @property
    def datagram(self):
        return self.multiplier

    @datagram.setter
    def datagram(self, value):
        self.multiplier = value

    @math(MathTargets.Damage)
    @check_object
    def calculate_damage(self, value: float, **kwargs):
        return value * self.multiplier

    @listen(Events.DamagePartDealt)
    def dealt_damage(self, author: Avatar = None, source: int = -1, **kwargs):
        if author is not self.parent_avatar:
            return

        if source == DamageSources.Sound:
            state = self.true_parent_cluster
            state.create_effect(self.parent_avatar, ClashEffects.Winded)


@CFReg.register(ClashEffects.Winded)
class EffectWinded(StatusEffectTimed):
    @math(MathTargets.Damage)
    @check_object
    @check_source(DamageSources.Sound)
    def calculate_damage(self, value: float = 1.1, **kwargs):
        if self.turns < 3:
            return value * 0.5
        return value

    @replace(ReplaceTargets.CreateEffect)
    def replace_encore_creation(self, avatar: Avatar, effect_id: int, **kwargs):
        if avatar is not self.parent_avatar or effect_id is not ClashEffects.Encore:
            return FizzleReplace


@CFReg.register(ClashEffects.SkelecogReduction)
class EffectSkelecogReduction(StatusEffect):
    def __init__(self, parent, stacks=1, **kwargs):
        super().__init__(parent, **kwargs)
        self.stacks = stacks

    @property
    def datagram(self):
        return self.stacks

    @datagram.setter
    def datagram(self, value):
        self.stacks = value

    @math(MathTargets.EffectRounds)
    @check_subject
    def calculate_effect_rounds(self, value: int, **kwargs):
        return value - self.stacks
