import subprocess
import sys
import time
import unittest

import sneakersync.main

import test_synchronize_base

class TestMain(test_synchronize_base.TestSynchronizeBase):
    def test_send_receive(self):
        self.drives[0].rename(self.drive)
        
        # with (self.drive / "module_1" / "new").open("w") as fd:
        #     fd.write("new file")
        (self.drive / "module_1" / "foo.1").unlink()
        # with (self.drive / "module_3" / "foo.3").open("w") as fd:
        #     fd.write("Modified file")
        # subprocess.check_call([
        #     "touch", "-a", "-t", "2001" "02" "03" "23" "24" ".25",
        #     self.drive / "module_1" / "subdir" / "bar.1"])
        # subprocess.check_call([
        #     "touch", "-m", "-t", "2002" "03" "04" "22" "21" ".20",
        #     self.drive / "module_3" / "bar.3"])
        
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
