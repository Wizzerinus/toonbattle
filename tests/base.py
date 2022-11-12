import logging
from unittest import TestCase


class BaseTest(TestCase):
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eq = self.assertEqual
        self.flt = self.assertAlmostEqual
