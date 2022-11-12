from toonbattle.calculator.common.attacks import TrackConfiguration
from toonbattle.calculator.helpers.enums import ClashGags

ClashGagConfiguration = {
    ClashGags.ToonUp: TrackConfiguration(0.95, (8, 15, 26, 45, 60, 84, 90, 135)),
    ClashGags.Trap: TrackConfiguration(1.0, (20, 35, 50, 75, 115, 160, 220, 280)),
    ClashGags.Lure: TrackConfiguration(
        (0.7, 0.6, 0.75, 0.65, 0.8, 0.7, 0.85, 0.75),
        (5, 10, 15, 30, 55, 45, 100, 75),
        rounds=(2, 2, 3, 3, 4, 4, 5, 5),
    ),
    ClashGags.Squirt: TrackConfiguration(0.95, (4, 8, 12, 21, 30, 56, 85, 115), rounds=(3, 3, 3, 3, 4, 4, 4, 4)),
    ClashGags.Zap: TrackConfiguration(1.0, (12, 22, 40, 62, 92, 140, 200, 250)),
    ClashGags.Throw: TrackConfiguration(0.75, (8, 13, 20, 35, 55, 90, 130, 170)),
    ClashGags.Sound: TrackConfiguration(0.95, (5, 10, 16, 23, 30, 50, 70, 90)),
    ClashGags.Drop: TrackConfiguration(0.6, (15, 25, 40, 60, 90, 140, 200, 240)),
}

ToonupMissMultiplier = 0.4
ToonupSelfHeal = 0.4

TrapExecutiveBoost = 1.3
TrapPrestigeBoost = 1.2

PrestigeLureSingleTargetBoost = 1.15
PrestigeLureAoEBoost = 1.25

SquirtPrestigeSplashDamage = 0.3
SquirtSplashDamage = 0.15
SquirtComboDamage = 0.2

ZapUnprestigePool = 0.9
ZapPrestigePool = 1.1

EncoreUnprestigeValue = 1.1
EncorePrestigeValue = 1.2

ThrowPrestigeHealingValue = 0.2
ThrowComboDamage = 0.2

DropComboDamage = 0.3
DropDebuffMultiplier = 1.15
