import sys
import time
import unittest

import sneakersync.main

import test_synchronize_base

class TestMain(test_synchronize_base.TestSynchronizeBase):
    def test_send_receive(self):
        self.drives[0].rename(self.drive)
        sys.argv = [sys.argv[0], "send", str(self.sneakerdrive)]
        sneakersync.main.main()
        self.drive.rename(self.drives[0])
        
        time.sleep(1)
        
        self.drives[1].rename(self.drive)
        sys.argv = [sys.argv[0], "receive", str(self.sneakerdrive)]
        sneakersync.main.main()
        self.drive.rename(self.drives[1])
        
        self._check_synchronized()

if __name__ == "__main__":
    sys.exit(unittest.main())
