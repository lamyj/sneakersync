class SneakersyncException(Exception):
    """Base class for sneakersync exceptions."""
    def __init__(self, action, module, text):
        Exception.__init__(self)
        self.action = action
        self.module = module
        self.text = text
