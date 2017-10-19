import unittest

import sneakersync

class TestRsync(unittest.TestCase):
    def test_get_filters(self):
        filters = [
            {"exclude": "/home/john.doe/.firefox/caches"},
            {"exclude": "*.pyc"}]
        rsync_args = sneakersync.get_filters(filters)
        self.assertSequenceEqual(
            rsync_args, [
                "--exclude", "/home/john.doe/.firefox/caches", 
                "--exclude", "*.pyc"])

if __name__ == "__main__":
    unittest.main()
