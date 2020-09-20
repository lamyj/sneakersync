import os
import pathlib
import socket
import tempfile
import unittest
import unittest.mock

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
        
        with self.path.open("w") as fd:
            fd.write("modules: [{root: {hostname: foo/bar}}]")
        
        with self.assertRaises(Exception):
            sneakersync.operations.read_configuration(self.path)
    
    def test_no_filter(self):
        with self.path.open("w") as fd:
            fd.write("modules: [{root: /foo/bar}]")
        with unittest.mock.patch("socket.gethostname", lambda: "host.name"):
            configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(
            configuration["modules"], 
            [{"root": {"host.name": pathlib.Path("/foo/bar")}, "filters": []}])
        self.assertSequenceEqual(configuration["filters"], [])
        
        with self.path.open("w") as fd:
            fd.write("modules: [{root: {hostname: /foo/bar}}]")
        configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(
            configuration["modules"], 
            [{"root": {"hostname": pathlib.Path("/foo/bar")}, "filters": []}])
        self.assertSequenceEqual(configuration["filters"], [])
    
    def test_module_filter(self):
        with self.path.open("w") as fd:
            fd.write(
                "modules: [{root: /foo/bar, filters: [{exclude: foo.pyc}]}]")
        with unittest.mock.patch("socket.gethostname", lambda: "host.name"):
            configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(
            configuration["modules"], [{
                "root": {"host.name": pathlib.Path("/foo/bar")}, 
                "filters": [{"exclude": "foo.pyc"}]}])
        self.assertSequenceEqual(
            configuration["filters"], [])
        
        with self.path.open("w") as fd:
            fd.write(
                "modules: [{root: {hostname: /foo/bar}, "
                "filters: [{exclude: foo.pyc}]}]")
        configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(
            configuration["modules"], [{
                "root": {"hostname": pathlib.Path("/foo/bar")}, 
                "filters": [{"exclude": "foo.pyc"}]}])
        self.assertSequenceEqual(
            configuration["filters"], [])
    
    def test_module_filter(self):
        with self.path.open("w") as fd:
            fd.write(
                "{modules: [{root: /foo/bar}], "
                "filters: [{exclude: foo.pyc}]}")
        with unittest.mock.patch("socket.gethostname", lambda: "host.name"):
            configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(
            configuration["modules"], 
            [{"root": {"host.name": pathlib.Path("/foo/bar")}, "filters": []}])
        self.assertSequenceEqual(
            configuration["filters"], [{"exclude": "foo.pyc"}])
        
        with self.path.open("w") as fd:
            fd.write(
                "{modules: [{root: {hostname: /foo/bar}}], "
                "filters: [{exclude: foo.pyc}]}")
        configuration = sneakersync.operations.read_configuration(self.path)
        self.assertSequenceEqual(
            configuration["modules"], 
            [{"root": {"hostname": pathlib.Path("/foo/bar")}, "filters": []}])
        self.assertSequenceEqual(
            configuration["filters"], [{"exclude": "foo.pyc"}])

if __name__ == "__main__":
    unittest.main()
