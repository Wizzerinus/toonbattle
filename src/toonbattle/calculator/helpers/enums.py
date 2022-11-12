from enum import IntEnum, auto


class ClashEffects(IntEnum):
    Cheer = auto()
    Trapped = auto()
    Dazed = auto()
    Lured = auto()
    Soak = auto()
    Encore = auto()
    Winded = auto()
    SkelecogReduction = auto()


class ClashGags(IntEnum):
    ToonUp = 0  # have to start from 0 here, sadly
    Trap = auto()
    Lure = auto()
    Squirt = auto()
    Zap = auto()
    Throw = auto()
    Sound = auto()
    Drop = auto()


class CommonEffects(IntEnum):
    Stun = 100
    ToonsHit = auto()


class MathTargets(IntEnum):
    Damage = auto()
    Accuracy = auto()
    EffectRounds = auto()
    Healing = auto()
    Knockback = auto()


class ReplaceTargets(IntEnum):
    CreateEffect = auto()
    DealDamage = auto()
    GagAccuracy = auto()
    Heal = auto()


class Events(IntEnum):
    ToonsMoved = auto()
    CogsMoved = auto()
    DamageDealt = auto()
    DamagePartDealt = auto()


class DamageSources(IntEnum):
    ToonUp = auto()
    Trap = auto()
    Sound = auto()
    Throw = auto()
    Squirt = auto()
    Zap = auto()
    Drop = auto()

    TrappedEffect = auto()
    SquirtSplash = auto()
    ZapPool = auto()
    Caramelize = auto()


class ExtraSources(IntEnum):
    ComboDamage = auto()


class AuxillaryObjects(IntEnum):
    State = auto()
    AvatarHolder = auto()
    Cog = auto()
    Toon = auto()
    StatusEffectController = auto()
    GagController = auto()
