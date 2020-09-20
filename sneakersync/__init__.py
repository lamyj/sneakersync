import logging
import socket
import sys

def get_module_root(module, host=None):
    if host is None:
        host = socket.gethostname()
    if host not in module["root"]:
        raise Exception(
            "Unknown host {} (should be one of {})".format(
                host, ", ".join(module["root"].keys())))
    
    return module["root"][host]

from .exception import SneakersyncException
import sys
sys.modules["sneakersync"].Exception = SneakersyncException

logger = logging.getLogger(__name__)

from . import operations, rsync
from .state import State
