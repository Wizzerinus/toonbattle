import logging
from math import ceil

from toonbattle.calculator.clash import gag_config
from toonbattle.calculator.clash.cogs import ClashCog
from toonbattle.calculator.common.attacks import GagController, GagDefinition, GagPart
from toonbattle.calculator.common.avatar import Avatar, AvatarHolder
from toonbattle.calculator.helpers.enums import (
    AuxillaryObjects,
    ClashEffects,
    ClashGags,
    CommonEffects,
    DamageSources,
    ExtraSources,
    MathTargets,
)
from toonbattle.calculator.globals import ClashGagRegistry as CGReg, ClashObjectRegistry as COReg

COReg.bind(AuxillaryObjects.GagController, GagController)
# (toon_avid, track 0-indexed, level 0-indexed, target_avid, prestige)
ClashGagTuple = tuple[int, int, int, int | str | tuple[int, ...], bool]


class ClashGagPart(GagPart):
    prestige: bool

    def __init__(self, toons: AvatarHolder, targets: AvatarHolder, gag: ClashGagTuple):
        author_avid, track, self.level, target_avid, self.prestige = gag
        self.author = toons[author_avid]

        if not isinstance(target_avid, tuple):
            target_avid = (target_avid,)
        self.target = tuple(targets[avid] for avid in target_avid)

    def __repr__(self):
        return f"({self.level},{self.prestige}) <- {self.author}({self.author.avatar_id})"


class ClashGagDefinition(GagDefinition):
    configuration = gag_config.ClashGagConfiguration
    gag_parts: list[ClashGagPart]
    target: tuple[ClashCog, ...]

    def get_damage_value(self, part: ClashGagPart) -> float:
        return self.configuration[self.track].damages[part.level]

    def perform_attack(self, combo: float = 0.0, aoe: bool = False, **kwargs) -> list[tuple[ClashGagPart, float]]:
        hit_cogs = [self.target[0]] if not aoe else self.true_parent_cluster.cogs
        damages = []
        for part in self.gag_parts:
            value = self.get_damage_value(part)
            damages.append((part, value))

        for cog in hit_cogs:
            total_damage = self.true_parent_cluster.deal_damage(
                cog, *[(damage, dict(author=part.author)) for part, damage in damages], **kwargs
            )
            self.true_parent_cluster.create_effect(cog, CommonEffects.Stun, stacks=len(damages))
            if combo and len(damages) > 1:
                total_damage *= combo
                self.true_parent_cluster.deal_damage(
                    cog, total_damage, author=self, extra_source=ExtraSources.ComboDamage, **kwargs
                )

        return damages


@CGReg.register(ClashGags.ToonUp)
class ToonUp(ClashGagDefinition):
    targets_toons = True

    def apply_hit(self):
        target_toons = self.apply_heal()
        for toon in target_toons:
            state = self.true_parent_cluster
            state.create_effect(toon, ClashEffects.Cheer)

    def apply_miss(self):
        self.apply_heal(gag_config.ToonupMissMultiplier)

    def apply_heal(self, multiplier: float = 1):
        gag = self.gag_parts[0]
        damage = self.configuration[self.track].damages[gag.level] * multiplier
        state = self.true_parent_cluster
        if self.gag_parts[0].prestige:
            self_heal = damage * gag_config.ToonupSelfHeal
            state.heal(self.gag_parts[0].author, self_heal, source=DamageSources.ToonUp)

        if self.max_level % 2 == 0:
            state.heal(self.target[0], damage, source=DamageSources.ToonUp)
            return self.target
        else:
            all_toons = [toon for toon in state.toons if toon is not self.gag_parts[0].author]
            for toon in all_toons:
                state.heal(toon, damage / len(all_toons), source=DamageSources.ToonUp)
            return all_toons


@CGReg.register(ClashGags.Trap)
class Trap(ClashGagDefinition):
    def get_accuracy(self, other_self):
        cog = self.target[0]
        return int(ClashEffects.Trapped not in cog.effects and ClashEffects.Lured not in cog.effects)

    def apply_hit(self):
        state = self.true_parent_cluster
        cog = self.target[0]
        state.create_effect(cog, CommonEffects.Stun, stacks=len(self.gag_parts))

        if len(self.gag_parts) > 1:
            return

        gag = self.gag_parts[0]
        damage = self.configuration[self.track].damages[gag.level]
        if cog.executive:
            damage *= gag_config.TrapExecutiveBoost
        if gag.prestige:
            damage *= gag_config.TrapPrestigeBoost

        damage = state.calculate(MathTargets.Damage, damage, source=DamageSources.Trap, subject=cog, author=gag.author)
        state.create_effect(cog, ClashEffects.Trapped, value=damage)


@CGReg.register(ClashGags.Lure)
class Lure(ClashGagDefinition):
    def get_damage(self, gag: ClashGagPart) -> int:
        base_damage = self.configuration[self.track].damages[gag.level]
        if gag.prestige:
            if gag.level % 2:
                base_damage *= gag_config.PrestigeLureAoEBoost
            else:
                base_damage *= gag_config.PrestigeLureSingleTargetBoost
        return ceil(base_damage)

    def apply_hit(self):
        state = self.true_parent_cluster
        for cog in self.target:
            gags = [gag for gag in self.gag_parts if gag.target == () or cog in gag.target]
            if not gags:
                continue

            max_damage = max(self.get_damage(gag) for gag in gags)
            max_rounds = max(self.configuration[self.track].extras["rounds"][gag.level] for gag in gags)
            state.create_effect(cog, ClashEffects.Lured, knockback=max_damage, rounds=max_rounds)


@CGReg.register(ClashGags.Squirt)
class Squirt(ClashGagDefinition):
    def apply_hit(self):
        damages = self.perform_attack(combo=gag_config.SquirtComboDamage, source=DamageSources.Squirt)
        cogs = self.true_parent_cluster.cogs
        index = cogs.index(self.target[0])
        state = self.true_parent_cluster

        # calculate splash damage
        splash_damage = 0
        for gag, value in damages:
            if gag.prestige:
                splash_damage += value * gag_config.SquirtPrestigeSplashDamage
            else:
                splash_damage += value * gag_config.SquirtSplashDamage

        # apply soak and splash damage
        rounds = self.configuration[self.track].extras["rounds"][self.max_level]
        state.create_effect(self.target[0], ClashEffects.Soak, turns=rounds)
        for cog in [cogs(index + 1), cogs(index - 1)]:
            if cog is None:
                continue

            state.deal_damage(cog, splash_damage, source=DamageSources.SquirtSplash)
            state.create_effect(cog, ClashEffects.Soak, turns=rounds)


@CGReg.register(ClashGags.Zap)
class Zap(ClashGagDefinition):
    logger = logging.getLogger("toonbattle.clash.gags.Zap")

    def reduce_soak(self, cog: Avatar):
        if ClashEffects.Soak not in cog.effects:
            self.logger.warning(f"{cog} does not have soak effect")
            return

        soak_effect = cog.effects[ClashEffects.Soak]
        soak_effect.turns = 0

    def get_accuracy(self, other_self):
        return int(ClashEffects.Soak in self.target[0].effects)

    def apply_hit(self):
        cog = self.target[0]
        state = self.true_parent_cluster
        index = state.cogs.index(cog)
        zap_options = [
            (cog, state.cogs(index + 1), state.cogs(index + 2)),
            (cog, state.cogs(index + 1)),
            (cog, state.cogs(index - 1), state.cogs(index - 2)),
            (cog, state.cogs(index - 1)),
            (cog,),
        ]
        for cogs in zap_options:
            # make sure all of these cogs are soaked
            if not all(cog is not None and ClashEffects.Soak in cog.effects for cog in cogs):
                continue

            damages = self.perform_attack(source=DamageSources.Zap)
            self.reduce_soak(self.target[0])
            if len(cogs) == 1:
                break

            # deal pool damage if > 1 cog was zapped
            damaged_by_pool = cogs[1:]
            total_damage = sum(damage for _, damage in damages)
            if self.gag_parts[0].prestige:
                total_damage *= gag_config.ZapPrestigePool
            else:
                total_damage *= gag_config.ZapUnprestigePool
            total_damage /= len(damaged_by_pool)
            for cog2 in damaged_by_pool:
                self.reduce_soak(cog2)
                state.deal_damage(cog2, total_damage, source=DamageSources.ZapPool)
            break

    def apply_miss(self):
        cog = self.target[0]
        if effect := cog.effects.get(ClashEffects.Lured):
            cog.effects.remove(effect)


@CGReg.register(ClashGags.Throw)
class Throw(ClashGagDefinition):
    def apply_hit(self):
        self.perform_attack(combo=gag_config.ThrowComboDamage, source=DamageSources.Throw)
        state = self.true_parent_cluster
        for gag in self.gag_parts:
            if gag.prestige:
                state.heal(
                    gag.author,
                    self.configuration[self.track].damages[gag.level] * gag_config.ThrowPrestigeHealingValue,
                    source=DamageSources.Caramelize,
                )


@CGReg.register(ClashGags.Sound)
class Sound(ClashGagDefinition):
    def apply_hit(self):
        self.perform_attack(source=DamageSources.Sound, aoe=True)
        state = self.true_parent_cluster
        for gag in self.gag_parts:
            if gag.prestige:
                encore = gag_config.EncorePrestigeValue
            else:
                encore = gag_config.EncoreUnprestigeValue
            state.create_effect(gag.author, ClashEffects.Encore, multiplier=encore)


@CGReg.register(ClashGags.Drop)
class Drop(ClashGagDefinition):
    def get_accuracy(self, other_self):
        target_cog = self.target[0]
        if ClashEffects.Lured in target_cog.effects:
            return 0

        return super().get_accuracy()

    def apply(self):
        # copied perform_attack due to separate accuracy calculation
        cog = self.target[0]
        damages = []
        hitting_gags = []
        for part in self.gag_parts:
            value = self.get_damage_value(part)
            if self.hit:
                damages.append((part, value))
                hitting_gags.append(part)

        total_damage = self.true_parent_cluster.deal_damage(
            cog, *[(damage, dict(author=part.author)) for part, damage in damages], source=DamageSources.Drop
        )
        if len(damages) > 1:
            total_damage *= gag_config.DropComboDamage
            self.true_parent_cluster.deal_damage(
                cog, total_damage, author=self, extra_source=ExtraSources.ComboDamage, source=DamageSources.Drop
            )

        return bool(hitting_gags)

    def get_damage_value(self, part: ClashGagPart) -> float:
        val = super().get_damage_value(part)
        if part.prestige:
            debuffs = [ClashEffects.Lured, ClashEffects.Soak]
            if any(debuff in cog.effects for cog in self.target for debuff in debuffs):
                val *= gag_config.DropDebuffMultiplier

        return val
