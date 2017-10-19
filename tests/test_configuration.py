import os
import tempfile
import unittest

import sneakersync

class TestConfiguration(unittest.TestCase):
    def test_default(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            configuration = sneakersync.read_configuration(path)
            self.assertSequenceEqual(configuration["modules"], [])
            self.assertSequenceEqual(configuration["filters"], [])
        finally:
            os.remove(path)
    
    def test_no_filter(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, "modules: [{root: /foo/bar}]")
        os.close(fd)
        try:
            configuration = sneakersync.read_configuration(path)
            self.assertSequenceEqual(
                configuration["modules"], 
                [{"root": "/foo/bar", "filters": []}])
            self.assertSequenceEqual(configuration["filters"], [])
        finally:
            os.remove(path)
    
    def test_module_filter(self):
        fd, path = tempfile.mkstemp()
        os.write(
            fd, "modules: [{root: /foo/bar, filters: [{exclude: foo.pyc}]}]")
        os.close(fd)
        try:
            configuration = sneakersync.read_configuration(path)
            self.assertSequenceEqual(
                configuration["modules"], 
                [{"root": "/foo/bar", "filters": [{"exclude": "foo.pyc"}]}])
            self.assertSequenceEqual(
                configuration["filters"], [])
        finally:
            os.remove(path)
    
    def test_module_filter(self):
        fd, path = tempfile.mkstemp()
        os.write(
            fd, "{modules: [{root: /foo/bar}], filters: [{exclude: foo.pyc}]}")
        os.close(fd)
        try:
            configuration = sneakersync.read_configuration(path)
            self.assertSequenceEqual(
                configuration["modules"], [{"root": "/foo/bar", "filters": []}])
            self.assertSequenceEqual(
                configuration["filters"], [{"exclude": "foo.pyc"}])
        finally:
            os.remove(path)
        

if __name__ == "__main__":
    unittest.main()
