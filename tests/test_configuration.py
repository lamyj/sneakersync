import os
import pathlib
import tempfile
import unittest

import sneakersync

class TestConfiguration(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        self.path = pathlib.Path(path)
    
    def tearDown(self):
        self.path.unlink()
    
    def test_default(self):
        configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(configuration["modules"], [])
        self.assertSequenceEqual(configuration["filters"], [])
    
    def test_non_absolute_path(self):
        with self.path.open("w") as fd:
            fd.write("modules: [{root: foo/bar}]")
        
        with self.assertRaises(Exception):
            sneakersync.operations.read_configuration(self.path)
    
    def test_no_filter(self):
        with self.path.open("w") as fd:
            fd.write("modules: [{root: /foo/bar}]")
        
        configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(
            configuration["modules"], 
            [{"root": pathlib.Path("/foo/bar"), "filters": []}])
        self.assertSequenceEqual(configuration["filters"], [])
    
    def test_module_filter(self):
        with self.path.open("w") as fd:
            fd.write("modules: [{root: /foo/bar, filters: [{exclude: foo.pyc}]}]")
        
        configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(
            configuration["modules"], 
            [{"root": pathlib.Path("/foo/bar"), "filters": [{"exclude": "foo.pyc"}]}])
        self.assertSequenceEqual(
            configuration["filters"], [])
    
    def test_module_filter(self):
        with self.path.open("w") as fd:
            fd.write("{modules: [{root: /foo/bar}], filters: [{exclude: foo.pyc}]}")
        
        configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(
            configuration["modules"], 
            [{"root": pathlib.Path("/foo/bar"), "filters": []}])
        self.assertSequenceEqual(
            configuration["filters"], [{"exclude": "foo.pyc"}])

if __name__ == "__main__":
    unittest.main()
