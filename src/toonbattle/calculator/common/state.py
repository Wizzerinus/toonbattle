import abc
from math import ceil
from typing import Sequence, Union, cast

from pycluster.messenger.cluster import MessageCluster
from pycluster.messenger.helpers import listen, replaceable
from pycluster.messenger.object_registry import ObjectRegistry

from toonbattle.calculator.clash.gags import ClashGagPart, ClashGagTuple
from toonbattle.calculator.common.attacks import GagController, GagDefinition
from toonbattle.calculator.common.avatar import Avatar, AvatarHolder, Cog, Toon
from toonbattle.calculator.helpers.enums import AuxillaryObjects, Events, MathTargets, ReplaceTargets
from toonbattle.calculator.globals import CalculationObject, ClashEffectRegistry, ClashGagRegistry, ClashObjectRegistry
from toonbattle.calculator.common.status_effects import StatusEffect, StatusEffectController


class CalculationState(CalculationObject, MessageCluster):
    StatusEffectRegistry: ObjectRegistry = None
    GagRegistry: ObjectRegistry = None
    RegistryObject: ObjectRegistry = None
    LatestAllocatedID = 100

    def __init__(self, registry=None):
        MessageCluster.__init__(self, self.RegistryObject)
        self.toons = self.registry.create_and_insert(
            AuxillaryObjects.AvatarHolder, self, "toons", cast_to=AvatarHolder, subclass_id=AuxillaryObjects.Toon
        )
        self.cogs = self.registry.create_and_insert(
            AuxillaryObjects.AvatarHolder, self, "cogs", cast_to=AvatarHolder, subclass_id=AuxillaryObjects.Cog
        )
        self.effects = self.registry.create_and_insert(
            AuxillaryObjects.StatusEffectController, self, "effects", cast_to=StatusEffectController
        )

    @replaceable(ReplaceTargets.CreateEffect)
    def create_effect(self, avatar: Union[Avatar, "CalculationState"], effect_id: int, **kwargs):
        parent = avatar.effects
        current_effect = parent.get(effect_id)
        if current_effect:
            current_effect.update(**kwargs)
            return current_effect

        # have to use parent here because the effect registry != the object registry!
        effect = parent.registry.create_and_insert(effect_id, parent, str(effect_id), **kwargs, cast_to=StatusEffect)
        return effect

    @replaceable(ReplaceTargets.DealDamage)
    def deal_damage_singular(self, avatar: Avatar, value: float, **kwargs):
        value = self.calculate(MathTargets.Damage, value, subject=avatar, **kwargs)
        avatar.health -= ceil(value)
        return value

    def deal_damage(self, avatar: Avatar, *sequence: float | tuple[float, dict], **common_kwargs):
        total_value = 0
        for item in sequence:
            if isinstance(item, tuple):
                damage, kwargs = item
            else:
                damage = item
                kwargs = {}
            total_value += self.deal_damage_singular(avatar, damage, **kwargs, **common_kwargs)
            self.emit(Events.DamagePartDealt, subject=avatar, damage=ceil(total_value), **kwargs, **common_kwargs)

        self.emit(Events.DamageDealt, subject=avatar, damage=ceil(total_value), **common_kwargs)
        return total_value

    @replaceable(ReplaceTargets.Heal)
    def heal(self, avatar: Avatar, value: float, overheal: bool = False, **kwargs):
        value = self.calculate(MathTargets.Healing, value, subject=avatar, **kwargs)
        if not overheal:
            value = min(value, avatar.max_health - avatar.health)
        avatar.health += ceil(value)
        return value

    def allocate(self) -> str:
        self.LatestAllocatedID += 1
        return str(self.LatestAllocatedID)

    @property
    def datagram(self):
        return self.LatestAllocatedID

    @datagram.setter
    def datagram(self, value):
        self.LatestAllocatedID = value

    @listen(Events.ToonsMoved)
    def toons_moved(self):
        self.cogs.remove_dead_avatars()

    @listen(Events.CogsMoved)
    def cogs_moved(self):
        self.toons.remove_dead_avatars()

    def create_cog(self, level: int, **kwargs) -> Cog:
        cls = cast(Cog, self.registry.objects[AuxillaryObjects.Cog])
        return cls.from_level(self.cogs, level=level, **kwargs)

    def create_toon(self) -> Toon:
        return self.toons.create(max_health=150)

    def run_gags(self, *pregags: tuple) -> list[GagDefinition]:
        hitting_gags = []
        with self.registry.temporary_object(AuxillaryObjects.GagController, self) as gag_ctrl:
            gags = self.get_gag_parts(gag_ctrl, pregags)
            gags = sorted(gags, key=lambda _gag: _gag.priority)
            for i, gag in enumerate(gags):
                gag_ctrl.add_child(str(i), gag)
                if gag.apply():
                    hitting_gags.append(gag)
        return hitting_gags

    def use_gags(self, *pregags: tuple) -> list[GagDefinition]:
        ans = self.run_gags(*pregags)
        self.emit(Events.ToonsMoved)
        return ans

    @abc.abstractmethod
    def get_gag_parts(self, gag_ctrl: GagController, gags: Sequence[tuple]) -> list[GagDefinition]:
        pass


@ClashObjectRegistry.register(0)
class ClashState(CalculationState):
    from toonbattle.calculator.clash import effects as _e, gags as _g, cogs as _c  # noqa: F401

    StatusEffectRegistry = ClashEffectRegistry
    RegistryObject = ClashObjectRegistry
    GagRegistry = ClashGagRegistry

    @staticmethod
    def build_merged_tracks(gags):
        track_split = []
        for track_id in range(8):
            gags_of_track = [gag for gag in gags if gag[1] == track_id]
            if gags_of_track:
                if any(gag[3] == () for gag in gags_of_track):
                    track_split.append((track_id, (), gags_of_track))
                else:
                    all_targets = {gag[3] for gag in gags_of_track}
                    for targets in all_targets:
                        track_split.append((track_id, targets, [gag for gag in gags_of_track if gag[3] == targets]))

        return track_split

    def get_gag_parts(self, gag_ctrl: GagController, gags: Sequence[ClashGagTuple]) -> list[GagDefinition]:
        def get_target_list(__track: int) -> AvatarHolder:
            return self.cogs if __track > 0 else self.toons

        def get_gag_weight(gag_pair: tuple[int, str | tuple, list]):
            av_ids = [x.avatar_id for x in get_target_list(gag_pair[0])]
            return gag_pair[0], (av_ids.index(gag_pair[1]) if gag_pair[1] != () else 0)

        # tracks = sorted({(gag[1], gag[3]) for gag in gags}, key=get_gag_weight)
        # track_split = [[gag for gag in gags if gag[1] == track and gag[3] == target] for track, target in tracks]
        track_split = sorted(self.build_merged_tracks(gags), key=get_gag_weight)

        gag_defs = []
        for index, (track, target, gag_list) in enumerate(track_split):
            gag_def = gag_ctrl.registry.create_and_insert(track, gag_ctrl, str(index), cast_to=GagDefinition)
            gag_parts = [ClashGagPart(self.toons, get_target_list(track), gag) for gag in gag_list]
            gag_def.construct(track, target, gag_parts)
            gag_defs.append(gag_def)
        return gag_defs
