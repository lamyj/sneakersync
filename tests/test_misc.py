from __future__ import print_function
import __builtin__
import io
import os
import tempfile
import unittest
import sys

import sneakersync

class TestMisc(unittest.TestCase):
    @staticmethod
    def raw_input(message, user_input):
        print(message)
        return user_input
    
    def test_confirm_yes(self):
        old_raw_input = __builtin__.raw_input
        
        sys.stdout = io.BytesIO()
        __builtin__.raw_input = lambda x: TestMisc.raw_input(x, "y")
        
        try:
            self.assertTrue(sneakersync.confirm("foo"))
            self.assertEqual(sys.stdout.getvalue().strip(), "foo [yn]")
        finally:
            __builtin__.raw_input = old_raw_input
            sys.stdout = sys.__stdout__
    
    def test_confirm_no(self):
        old_raw_input = __builtin__.raw_input
        
        sys.stdout = io.BytesIO()
        __builtin__.raw_input = lambda x: TestMisc.raw_input(x, "n")
        
        try:
            self.assertFalse(sneakersync.confirm("foo"))
            self.assertEqual(sys.stdout.getvalue().strip(), "foo [yn]")
        finally:
            __builtin__.raw_input = old_raw_input
            sys.stdout = sys.__stdout__

if __name__ == "__main__":
    unittest.main()
