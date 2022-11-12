import math
import unittest

from base import BaseTest
from toonbattle.calculator.clash import gag_config
from toonbattle.calculator.common.state import ClashState
from toonbattle.calculator.helpers.enums import ClashEffects, ClashGags, CommonEffects


class TestClashGags(BaseTest):
    def setUp(self):
        self.battle = ClashState()
        # ensure deterministic tests
        self.battle.create_effect(self.battle, CommonEffects.ToonsHit)
        # spawn some avatars
        self.toon1 = self.battle.create_toon()
        self.toon2 = self.battle.create_toon()
        self.toon3 = self.battle.create_toon()
        self.small_cog = self.battle.create_cog(10)
        self.big_cog = self.battle.create_cog(15)
        self.exe_cog = self.battle.create_cog(20, exe=True, attack_oriented=False)

    def tearDown(self):
        self.battle.cleanup()
        self.battle = None

    def toon_health_equals(self, a, b, c):
        a, b, c = math.ceil(a), math.ceil(b), math.ceil(c)
        self.eq(self.toon1.health, a)
        self.eq(self.toon2.health, b)
        self.eq(self.toon3.health, c)

    LipstickHeal = gag_config.ClashGagConfiguration[ClashGags.ToonUp].damages[2]
    JuggleHeal = gag_config.ClashGagConfiguration[ClashGags.ToonUp].damages[5] / 2
    SelfHeal = gag_config.ToonupSelfHeal

    def test_toonup(self):
        self.battle.deal_damage(self.toon1, 100)
        self.battle.deal_damage(self.toon3, 110)
        self.battle.deal_damage(self.toon2, 30)
        self.toon_health_equals(50, 120, 40)
        self.battle.run_gags((self.toon2.avatar_id, ClashGags.ToonUp, 2, self.toon1.avatar_id, False))
        self.toon_health_equals(50 + self.LipstickHeal, 120, 40)
        self.battle.run_gags((self.toon2.avatar_id, ClashGags.ToonUp, 2, self.toon3.avatar_id, True))
        post_selfheal = 120 + self.LipstickHeal * self.SelfHeal
        self.toon_health_equals(50 + self.LipstickHeal, post_selfheal, 40 + self.LipstickHeal)
        self.assertIn(ClashEffects.Cheer, self.toon1.effects, msg="Using toon-up triggers Cheer")
        self.assertNotIn(ClashEffects.Cheer, self.toon2.effects, msg="Self-heal does not trigger Cheer")
        self.assertIn(ClashEffects.Cheer, self.toon3.effects)

        self.battle.use_gags()
        self.assertNotIn(ClashEffects.Cheer, self.toon1.effects, msg="Cheer only exists for 1 turn")
        self.assertNotIn(ClashEffects.Cheer, self.toon3.effects)
        self.battle.deal_damage(self.toon1, self.LipstickHeal)
        self.battle.deal_damage(self.toon3, self.LipstickHeal)
        self.battle.run_gags(
            # intentionally passing a bogus avId to test that it's ignored
            (self.toon2.avatar_id, ClashGags.ToonUp, 5, self.toon1.avatar_id, False)
        )
        self.toon_health_equals(50 + self.JuggleHeal, post_selfheal, 40 + self.JuggleHeal)
        self.assertIn(ClashEffects.Cheer, self.toon1.effects, msg="Using multi-target toon-up triggers Cheer")
        self.assertNotIn(ClashEffects.Cheer, self.toon2.effects, msg="Multi-target Toon-up does not Cheer its user")
        self.assertIn(ClashEffects.Cheer, self.toon3.effects)

    MarblesDamage = gag_config.ClashGagConfiguration[ClashGags.Trap].damages[3]

    def test_trap1(self):
        self.battle.run_gags((self.toon2.avatar_id, ClashGags.Trap, 3, self.small_cog.avatar_id, False))
        self.assertIn(ClashEffects.Trapped, self.small_cog.effects, msg="Cog gets trapped")
        self.assertIn(CommonEffects.Stun, self.small_cog.effects, msg="Cog gets stunned")
        trap_effect = self.small_cog.effects[ClashEffects.Trapped]
        self.eq(trap_effect.value, self.MarblesDamage, msg="Trap damage is correct")
        self.battle.use_gags()
        self.assertNotIn(CommonEffects.Stun, self.small_cog.effects, msg="Stun wears off after 1 turn")
        self.battle.use_gags()
        self.battle.use_gags()
        self.battle.use_gags()
        self.assertIn(ClashEffects.Trapped, self.small_cog.effects, msg="Trap exists forever")

        self.battle.run_gags(
            (self.toon2.avatar_id, ClashGags.Trap, 3, self.big_cog.avatar_id, False),
            (self.toon1.avatar_id, ClashGags.Trap, 3, self.big_cog.avatar_id, False),
        )
        self.assertNotIn(ClashEffects.Trapped, self.big_cog.effects, msg="Cog can only be trapped once")
        stun_effect = self.big_cog.effects[CommonEffects.Stun]
        self.eq(stun_effect.stacks, 2, msg="Cog gets 2 stacks of stun")
        self.battle.use_gags()

        hit = self.battle.run_gags((self.toon2.avatar_id, ClashGags.Trap, 3, self.small_cog.avatar_id, False))
        self.assertEqual(len(hit), 0, msg="Trapped cog cannot be hit by another trap")
        self.assertIs(trap_effect, self.small_cog.effects[ClashEffects.Trapped], msg="Trap effect is the same")

    def test_trap2(self):
        self.battle.run_gags(
            (self.toon1.avatar_id, ClashGags.Trap, 3, self.small_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Trap, 3, self.big_cog.avatar_id, True),
        )
        self.assertIn(ClashEffects.Trapped, self.small_cog.effects, msg="Cog gets trapped")
        self.assertIn(ClashEffects.Trapped, self.big_cog.effects, msg="Trap merge accounts for different cogs")
        trap = self.big_cog.effects[ClashEffects.Trapped]
        self.eq(trap.value, self.MarblesDamage * gag_config.TrapPrestigeBoost, msg="Trap damage is boosted by prestige")

        self.battle.run_gags(
            (self.toon3.avatar_id, ClashGags.Trap, 3, self.exe_cog.avatar_id, True),
        )
        trap2 = self.exe_cog.effects[ClashEffects.Trapped]
        self.flt(
            trap2.value,
            self.MarblesDamage * gag_config.TrapPrestigeBoost * gag_config.TrapExecutiveBoost,
            msg="Trap damage is boosted multiplicatively",
        )

    MagnetKnockback = gag_config.ClashGagConfiguration[ClashGags.Lure].damages[3]
    TenDollarKnockback = gag_config.ClashGagConfiguration[ClashGags.Lure].damages[4]

    def test_lure(self):
        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Lure, 4, self.big_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Lure, 3, (), False),
        )
        self.assertIn(ClashEffects.Lured, self.big_cog.effects, msg="Cog gets lured")
        self.assertIn(ClashEffects.Lured, self.small_cog.effects, msg="Cog gets multi-lured")
        big_effect = self.big_cog.effects[ClashEffects.Lured]
        small_effect = self.small_cog.effects[ClashEffects.Lured]
        self.eq(small_effect.knockback, self.MagnetKnockback, msg="Multiple knockbacks are applied")
        self.eq(big_effect.knockback, self.TenDollarKnockback, msg="Lure knockback is correct")

    def test_trap_lure(self):
        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Lure, 4, self.big_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Trap, 3, self.big_cog.avatar_id, False),
        )
        self.assertNotIn(ClashEffects.Trapped, self.big_cog.effects, msg="Single-target lure removes trap")
        self.assertNotIn(ClashEffects.Lured, self.big_cog.effects, msg="Trap removes Single-target lure")
        self.eq(
            self.big_cog.max_health - self.big_cog.health,
            self.MarblesDamage,
            msg="Trap damage is dealt with single lures",
        )

        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Lure, 4, self.exe_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Trap, 3, self.exe_cog.avatar_id, False),
            (self.toon3.avatar_id, ClashGags.Lure, 4, self.exe_cog.avatar_id, False),
        )
        self.assertNotIn(ClashEffects.Lured, self.exe_cog.effects, msg="Lure does not happen twice on the same turn")
        self.eq(
            self.exe_cog.max_health - self.exe_cog.health,
            math.ceil(self.MarblesDamage * gag_config.TrapExecutiveBoost),
            msg="Trap damage is dealt only once",
        )

        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Lure, 3, (), False),
            (self.toon2.avatar_id, ClashGags.Trap, 3, self.small_cog.avatar_id, False),
        )
        self.assertNotIn(ClashEffects.Trapped, self.small_cog.effects, msg="Lure removes trap")
        self.assertNotIn(ClashEffects.Lured, self.small_cog.effects, msg="Trap removes lure")
        self.eq(self.small_cog.max_health - self.small_cog.health, self.MarblesDamage, msg="Trap damage is dealt")

    SeltzerBottleDamage = gag_config.ClashGagConfiguration[ClashGags.Squirt].damages[4]

    def test_squirt(self):
        self.battle.use_gags(
            (self.toon3.avatar_id, ClashGags.Lure, 3, (), False),
            (self.toon1.avatar_id, ClashGags.Squirt, 4, self.exe_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Squirt, 4, self.exe_cog.avatar_id, False),
        )
        self.assertIn(ClashEffects.Soak, self.exe_cog.effects, msg="Cog gets soaked")
        self.assertIn(ClashEffects.Soak, self.big_cog.effects, msg="Soak is applied in AoE fashion")
        self.assertNotIn(ClashEffects.Soak, self.small_cog.effects, msg="Soak does not apply with distance > 1")
        self.eq(
            self.exe_cog.max_health - self.exe_cog.health,
            math.ceil((self.SeltzerBottleDamage + self.MagnetKnockback) * (1 + gag_config.SquirtComboDamage) * 2),
            msg="Squirt applies combo damage",
        )
        self.eq(
            self.big_cog.max_health - self.big_cog.health,
            math.ceil(self.SeltzerBottleDamage * gag_config.SquirtSplashDamage * 2),
            msg="Squirt applies splash damage which does not combo or knockback",
        )
        self.eq(self.small_cog.max_health, self.small_cog.health, msg="Squirt does not apply to distant cogs")
        self.assertNotIn(ClashEffects.Lured, self.exe_cog.effects, msg="Squirt damage does knockback")
        self.assertIn(ClashEffects.Lured, self.big_cog.effects, msg="Splash damage does not knockback")

    StagelightDamage = gag_config.ClashGagConfiguration[ClashGags.Zap].damages[5]

    def test_zap(self):
        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Lure, 4, self.big_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Zap, 4, self.big_cog.avatar_id, False),
        )
        self.eq(self.big_cog.max_health, self.big_cog.health, msg="Zap does not hit unsoaked cogs even when lured")
        self.assertNotIn(ClashEffects.Lured, self.big_cog.effects, msg="Missing zap unlures the cogs")

        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Squirt, 4, self.big_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Zap, 5, self.big_cog.avatar_id, False),
        )
        self.eq(
            self.big_cog.max_health - self.big_cog.health,
            self.StagelightDamage + self.SeltzerBottleDamage,
            msg="Zap deals proper damage to soaked cogs",
        )
        splash_damage = math.ceil(self.SeltzerBottleDamage * gag_config.SquirtSplashDamage)
        self.eq(
            self.exe_cog.max_health - self.exe_cog.health,
            math.ceil(self.StagelightDamage * gag_config.ZapUnprestigePool) + splash_damage,
            msg="Zap deals proper damage to the far left cog",
        )
        self.eq(
            self.small_cog.max_health - self.small_cog.health, splash_damage, msg="Zap does not hit the far right cog"
        )
        self.assertNotIn(ClashEffects.Soak, self.big_cog.effects, msg="Zap removes soak")
        self.assertNotIn(ClashEffects.Soak, self.exe_cog.effects, msg="Zap removes soak from cogs hit by the pool")
        self.assertIn(ClashEffects.Soak, self.small_cog.effects, msg="Zap does not remove soak from the other cog")

    def test_zap_pt2(self):
        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Squirt, 4, self.big_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Zap, 5, self.exe_cog.avatar_id, True),
        )
        squirt_damage = self.SeltzerBottleDamage
        splash_damage = math.ceil(self.SeltzerBottleDamage * gag_config.SquirtSplashDamage)
        zap_damage = self.StagelightDamage
        pool_damage = math.ceil(self.StagelightDamage * gag_config.ZapPrestigePool / 2)
        self.eq(self.exe_cog.max_health - self.exe_cog.health, splash_damage + zap_damage)
        self.eq(self.big_cog.max_health - self.big_cog.health, squirt_damage + pool_damage)
        self.eq(self.small_cog.max_health - self.small_cog.health, splash_damage + pool_damage)

    FruitPieDamage = gag_config.ClashGagConfiguration[ClashGags.Throw].damages[4]

    def test_throw(self):
        self.battle.deal_damage(self.toon1, 50)
        self.battle.deal_damage(self.toon2, 50)
        self.battle.use_gags(
            (self.toon3.avatar_id, ClashGags.Lure, 3, (), False),
            (self.toon1.avatar_id, ClashGags.Throw, 4, self.exe_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Throw, 4, self.exe_cog.avatar_id, True),
        )
        self.eq(
            self.exe_cog.max_health - self.exe_cog.health,
            math.ceil((self.FruitPieDamage + self.MagnetKnockback) * (1 + gag_config.ThrowComboDamage) * 2),
            msg="Squirt applies combo damage",
        )
        self.eq(self.big_cog.max_health, self.big_cog.health, msg="Throw does not apply splash damage")
        self.assertNotIn(ClashEffects.Lured, self.exe_cog.effects, msg="Throw damage does knockback")
        self.eq(self.toon1.max_health - self.toon1.health, 50, msg="Throw does not heal toons")
        pres_heal = math.ceil(self.FruitPieDamage * gag_config.ThrowPrestigeHealingValue)
        self.eq(self.toon2.max_health - self.toon2.health, 50 - pres_heal, msg="Prestige throw heals")

    WhistleDamage = gag_config.ClashGagConfiguration[ClashGags.Sound].damages[1]

    def test_sound(self):
        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Sound, 1, (), False),
            (self.toon2.avatar_id, ClashGags.Sound, 1, (), True),
        )
        for cog in (self.exe_cog, self.small_cog, self.big_cog):
            self.eq(cog.max_health - cog.health, self.WhistleDamage * 2, msg="Sound does not apply combo damage")

        self.assertIn(ClashEffects.Encore, self.toon1.effects, msg="Sound applies encore (unpres)")
        self.assertIn(ClashEffects.Encore, self.toon2.effects, msg="Sound applies encore (pres)")
        self.flt(
            self.toon1.effects[ClashEffects.Encore].multiplier, gag_config.EncoreUnprestigeValue, msg="Encore (unpres)"
        )
        self.flt(
            self.toon2.effects[ClashEffects.Encore].multiplier, gag_config.EncorePrestigeValue, msg="Encore (pres)"
        )

        current_dealt_damage = math.ceil(
            self.WhistleDamage * (gag_config.EncorePrestigeValue + gag_config.EncoreUnprestigeValue + 2)
        )
        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Sound, 1, (), False),
            (self.toon2.avatar_id, ClashGags.Sound, 1, (), True),
        )
        for cog in (self.exe_cog, self.small_cog, self.big_cog):
            self.eq(cog.max_health - cog.health, current_dealt_damage, msg="Encore increases sound damage")

        self.assertNotIn(ClashEffects.Encore, self.toon1.effects, msg="Encore wears off")
        self.assertIn(ClashEffects.Winded, self.toon1.effects, msg="Encore gets replaced by Winded")

        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Sound, 1, (), False),
            (self.toon2.avatar_id, ClashGags.Sound, 1, (), True),
        )
        current_dealt_damage += self.WhistleDamage
        for cog in (self.exe_cog, self.small_cog, self.big_cog):
            self.eq(cog.max_health - cog.health, current_dealt_damage, msg="Winded reduces sound damage")

    PianoDamage = gag_config.ClashGagConfiguration[ClashGags.Drop].damages[7]

    def test_drop(self):
        self.battle.use_gags(
            (self.toon1.avatar_id, ClashGags.Lure, 2, self.small_cog.avatar_id, False),
            (self.toon2.avatar_id, ClashGags.Drop, 7, self.small_cog.avatar_id, False),
            (self.toon3.avatar_id, ClashGags.Drop, 7, self.exe_cog.avatar_id, True),
        )
        self.eq(self.small_cog.max_health, self.small_cog.health, msg="Drop cannot hit lured cogs")
        self.eq(self.exe_cog.max_health - self.exe_cog.health, self.PianoDamage, msg="Drop damages unlured cogs")

        self.battle.create_effect(self.big_cog, ClashEffects.Dazed)
        self.battle.create_effect(self.big_cog, ClashEffects.Soak)
        self.battle.use_gags(
            (self.toon3.avatar_id, ClashGags.Drop, 7, self.big_cog.avatar_id, True),
        )
        self.eq(
            self.big_cog.max_health - self.big_cog.health,
            math.ceil(self.PianoDamage * gag_config.DropDebuffMultiplier),
            msg="Drop prestige increases damage on dazed/soaked",
        )


if __name__ == "__main__":
    unittest.main()
