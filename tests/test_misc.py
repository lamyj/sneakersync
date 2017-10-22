from __future__ import print_function
import io
import os
import tempfile
import unittest
import sys

import six.moves

import sneakersync

class TestMisc(unittest.TestCase):
    @staticmethod
    def input(message, user_input):
        print(message)
        return user_input
    
    def test_confirm_yes(self):
        old_input = six.moves.input
        
        if sys.version_info.major >= 3:
            sys.stdout = io.StringIO()
        else:
            sys.stdout = io.BytesIO()
        six.moves.input = lambda x: TestMisc.input(x, "y")
        
        try:
            self.assertTrue(sneakersync.confirm("foo"))
            self.assertEqual(sys.stdout.getvalue().strip(), "foo [yn]")
        finally:
            six.moves.input = old_input
            sys.stdout = sys.__stdout__
    
    def test_confirm_no(self):
        old_input = six.moves.input
        
        if sys.version_info.major >= 3:
            sys.stdout = io.StringIO()
        else:
            sys.stdout = io.BytesIO()
        six.moves.input = lambda x: TestMisc.input(x, "n")
        
        try:
            self.assertFalse(sneakersync.confirm("foo"))
            self.assertEqual(sys.stdout.getvalue().strip(), "foo [yn]")
        finally:
            six.moves.input = old_input
            sys.stdout = sys.__stdout__

if __name__ == "__main__":
    unittest.main()
