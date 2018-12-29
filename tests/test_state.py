import os
import pathlib
import tempfile
import unittest

import sneakersync

class TestState(unittest.TestCase):
    def test_load_non_existant(self):
        state = sneakersync.state.State.load(pathlib.Path("/non_existant"))
        self.assertEqual(state.path, pathlib.Path("/non_existant"))
        self.assertEqual(state.previous_direction, None)
        self.assertEqual(state.previous_date, None)
        self.assertEqual(state.previous_host, None)
    
    def test_load_empty(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        path = pathlib.Path(path)
        
        try:
            state = sneakersync.state.State.load(path)
            self.assertEqual(state.path, path)
            self.assertEqual(state.previous_direction, None)
            self.assertEqual(state.previous_date, None)
            self.assertEqual(state.previous_host, None)
        finally:
            path.unlink()
    
    def test_save(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        path = pathlib.Path(path)
        
        try:
            state = sneakersync.state.State(path, "send", "now", "myself")
            state.save()
            
            other_state = sneakersync.state.State.load(path)
            
            self.assertEqual(state.path, other_state.path)
            self.assertEqual(
                state.previous_direction, other_state.previous_direction)
            self.assertEqual(state.previous_host, other_state.previous_host)
        finally:
            path.unlink()

if __name__ == "__main__":
    unittest.main()
