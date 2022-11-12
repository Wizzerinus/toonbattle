import logging
import typing
from typing import cast

from pycluster.messenger.message_object import MessageObject
from pycluster.messenger.object_registry import ObjectRegistry

if typing.TYPE_CHECKING:
    from toonbattle.calculator.common.state import CalculationState

ClashObjectRegistry = ObjectRegistry("clash-object")
ClashEffectRegistry = ObjectRegistry("clash-effect")
ClashGagRegistry = ObjectRegistry("clash-gag")


class CalculationObject(MessageObject):
    logger = logging.getLogger("toonbattle.calculator.CalculationObject")

    @property
    def parent_cluster(self) -> "CalculationState":
        return cast("CalculationState", super().parent_cluster)
