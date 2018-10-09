import logging
import sys

from .exception import SneakersyncException
import sys
sys.modules["sneakersync"].Exception = SneakersyncException

logger = logging.getLogger(__name__)

import operations
import rsync
