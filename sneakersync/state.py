import copy
import yaml

class State(object):
    """State of the sneakernet (previous operation, previous host, etc.)."""
    
    def __init__(self, path, previous_direction, previous_date, previous_host):
        self.path = path
        self.previous_direction = previous_direction
        self.previous_date = previous_date
        self.previous_host = previous_host
    
    def save(self):
        data = copy.copy(vars(self))
        del data["path"]
        with open(self.path, "w") as fd:
            yaml.dump(data, fd)
    
    @staticmethod
    def load(path):
        state = {
            "previous_direction": None,
            "previous_date": None,
            "previous_host": None,
        }
        
        if path.is_file():
            with path.open() as fd:
                data = yaml.load(fd)
                if data:
                    state.update(data)
        
        return State(path, **state)
