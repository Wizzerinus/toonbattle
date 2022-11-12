# ToonBattle

ToonBattle is a flexible modular battle simulator for various Toontown private servers.

## Features

* Support for toon attacks and status effects
* Modularity - ToonBattle is designed to be modular, allowing for easy addition of mechanics from new servers,
as well as new gags and manager battles. Right now only **Toontown: Corporate Clash** is implemented
  (using the 1.3 mechanic set).

## Installation

* Install Python 3.10 or higher
* Install [pycluster](https://github.com/multidragon/pycluster)

## Usage

### Programmatically

Battle can be created by using the `ClashState` class.
Afterwards, the attacks can be easily simulated using track IDs, for example:

```py
from toonbattle.calculator.common.state import ClashState
from toonbattle.calculator.helpers.enums import ClashGags, CommonEffects

battle = ClashState()
battle.create_effect(battle, CommonEffects.ToonsHit)
toon = battle.create_toon()
cog = battle.create_cog(level=12)
battle.run_gags(
    (toon.avatar_id, ClashGags.Throw, 7, cog.avatar_id, False)
)
assert cog.health == 182 - 170
```

### Web interface

Currently WIP.

## Future plans

* Implement the web interface
* Implement the combo finder for TTCC
* Implement cog attack AI and cog managers
* Support for Toontown: Event Horizon
