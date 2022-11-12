import json
import unittest

from base import BaseTest
from toonbattle.calculator.common.state import ClashState
from toonbattle.calculator.globals import ClashObjectRegistry
from toonbattle.calculator.helpers.enums import ClashEffects


class TestWrap(BaseTest):
    def setUp(self):
        self.s = ClashState()
        self.s.create_cog(15)
        self.s.create_cog(14)
        cog3 = self.s.create_cog(13)
        cog3.health = 181
        self.s.create_effect(cog3, ClashEffects.Dazed)

    def tearDown(self):
        self.s.cleanup()
        self.s = None

    def test_wrap(self):
        wrapped = json.loads(json.dumps(self.s.wrap()))
        s2 = ClashObjectRegistry.unwrap(wrapped)
        self.assertEqual(str(s2.cogs), str(self.s.cogs))
        s2.cleanup()


if __name__ == "__main__":
    unittest.main()
