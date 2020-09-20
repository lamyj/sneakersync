import socket
import subprocess
import sys
import time
import unittest
import unittest.mock

import sneakersync.main

import test_synchronize_base

class TestMain(test_synchronize_base.TestSynchronizeBase):
    def test_send_receive(self):
        with (self.drives[0] / "module_1" / "new").open("w") as fd:
            fd.write("new file")
        (self.drives[0] / "module_1" / "foo.1").unlink()
        with (self.drives[0] / "module_3" / "foo.3").open("w") as fd:
            fd.write("Modified file")
        subprocess.check_call([
            "touch", "-a", "-t", "2001" "02" "03" "23" "24" ".25",
            self.drives[0] / "module_1" / "subdir" / "bar.1"])
        subprocess.check_call([
            "touch", "-m", "-t", "2002" "03" "04" "22" "21" ".20",
            self.drives[0] / "module_3" / "bar.3"])
        
        with unittest.mock.patch("socket.gethostname", lambda: "first.host"):
            sys.argv = [sys.argv[0], "send", str(self.sneakerdrive)]
            sneakersync.main.main()
        
        time.sleep(1)
        
        with unittest.mock.patch("socket.gethostname", lambda: "second.host"):
            sys.argv = [sys.argv[0], "receive", str(self.sneakerdrive)]
            sneakersync.main.main()
        
        self._check_synchronized()

if __name__ == "__main__":
    sys.exit(unittest.main())
