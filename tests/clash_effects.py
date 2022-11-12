import unittest

from base import BaseTest
from toonbattle.calculator.common.avatar import Cog, Toon
from toonbattle.calculator.helpers.enums import ClashEffects, CommonEffects, DamageSources, Events, MathTargets
from toonbattle.calculator.common.state import ClashState


class TestClashEffects(BaseTest):
    battle: ClashState
    small_cog: Cog
    big_cog: Cog
    toon1: Toon
    toon2: Toon

    def setUp(self) -> None:
        self.battle = ClashState()
        self.toon1 = self.battle.create_toon()
        self.toon2 = self.battle.create_toon()
        self.small_cog = self.battle.create_cog(10)
        self.big_cog = self.battle.create_cog(15)
        self.exe_cog = self.battle.create_cog(20, exe=True, attack_oriented=False)

    def tearDown(self) -> None:
        self.battle.cleanup()

    def test_defense(self):
        acc = 0.7 + 0.5
        self.flt(
            self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.small_cog),
            0.75,
            msg="Toon accuracy is 0.7 + 0.5 = 1.2, but the cog has 0.45 (10 * 0.05 - 0.05) defense, so it's 0.75",
        )
        self.flt(
            self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.big_cog),
            0.55,
            msg="Defense caps at 0.65",
        )
        self.flt(
            self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.exe_cog),
            0.4,
            msg="Executive/defense cogs bypass defense cap",
        )

    def test_cheer(self):
        acc = 0.7 + 0.5
        self.flt(self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.big_cog), 0.55)
        self.battle.create_effect(self.toon1, ClashEffects.Cheer)

        self.flt(
            self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.big_cog),
            0.75,
            msg="Cheer increases accuracy by 0.2",
        )
        self.flt(
            self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon2, subject=self.big_cog),
            0.55,
            msg="Cheer only affects the toon that has it",
        )

        self.battle.emit(Events.ToonsMoved)
        self.flt(
            self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.big_cog),
            0.55,
            msg="Cheer only lasts one turn",
        )

    def test_trapped(self):
        acc = 0.7 + 0.5
        self.flt(self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.small_cog), 0.75)
        self.battle.create_effect(self.small_cog, ClashEffects.Trapped, value=100)
        self.battle.create_effect(self.small_cog, ClashEffects.Lured)
        self.eq(self.small_cog.health, 32, msg="Trap did 100 damage")
        self.eq(len(self.small_cog.effects), 1, msg="Trap removed itself and lure and added Dazed")
        self.flt(
            self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.small_cog),
            0.85,
            msg="Dazed cogs have 0.1 dodge down",
        )

        self.battle.emit(Events.ToonsMoved)
        self.flt(
            self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.small_cog),
            0.85,
            msg="Dazed lasts > 1 turn",
        )
        self.battle.emit(Events.ToonsMoved)
        self.flt(
            self.battle.calculate(MathTargets.Accuracy, acc, author=self.toon1, subject=self.small_cog),
            0.75,
            msg="Dazed wears off after 2 turns",
        )

    def test_encore(self):
        sound_damage = 50
        calc_damage = self.battle.calculate(
            MathTargets.Damage, sound_damage, author=self.toon1, subject=self.big_cog, source=DamageSources.Sound
        )
        self.eq(calc_damage, 50)
        self.battle.create_effect(self.toon1, ClashEffects.Encore, multiplier=1.2)
        self.battle.emit(Events.ToonsMoved)
        calc_damage = self.battle.calculate(
            MathTargets.Damage, sound_damage, author=self.toon1, subject=self.big_cog, source=DamageSources.Sound
        )
        self.eq(calc_damage, 60, msg="Encore increases damage by 20%")

        self.battle.emit(
            Events.DamagePartDealt,
            author=self.toon1,
            subject=self.big_cog,
            damage=calc_damage,
            source=DamageSources.Sound,
        )
        self.battle.emit(Events.ToonsMoved)

        calc_damage = self.battle.calculate(
            MathTargets.Damage, sound_damage, author=self.toon1, subject=self.big_cog, source=DamageSources.Sound
        )
        self.eq(calc_damage, 25, msg="Encore got replaced with Winded")
        calc_damage = self.battle.calculate(
            MathTargets.Damage, sound_damage, author=self.toon1, subject=self.big_cog, source=DamageSources.Throw
        )
        self.eq(calc_damage, 50, msg="Winded only affects sound damage")

        self.battle.emit(Events.ToonsMoved)
        calc_damage = self.battle.calculate(
            MathTargets.Damage, sound_damage, author=self.toon1, subject=self.big_cog, source=DamageSources.Sound
        )
        self.eq(calc_damage, 25, msg="Winded lasts > 1 turn")
        self.battle.create_effect(self.big_cog, ClashEffects.Encore, multiplier=1.2)
        calc_damage = self.battle.calculate(
            MathTargets.Damage, sound_damage, author=self.toon1, subject=self.big_cog, source=DamageSources.Sound
        )
        self.eq(len(self.big_cog.effects), 1, msg="Winded prevents Encore creation")
        self.eq(calc_damage, 25, msg="No other damage changes applied")

        self.battle.emit(Events.ToonsMoved)
        calc_damage = self.battle.calculate(
            MathTargets.Damage, sound_damage, author=self.toon1, subject=self.big_cog, source=DamageSources.Sound
        )
        self.eq(calc_damage, 50, msg="Winded wears off after 2 turns")

    def test_stun(self):
        stun = self.battle.create_effect(self.big_cog, CommonEffects.Stun)
        self.eq(stun.stacks, 1, msg="Stuns are created with 1 stack")
        stun2 = self.battle.create_effect(self.big_cog, CommonEffects.Stun)
        self.assertIs(stun, stun2, msg="Creating a stun when there's another stun replaces it")
        self.eq(stun.stacks, 2, msg="Stun stacks are added together")
        self.battle.emit(Events.ToonsMoved)
        self.eq(len(self.big_cog.effects), 0, msg="Stun wears off after 1 turn")


if __name__ == "__main__":
    unittest.main()
