import datetime
import fnmatch
import os
import pathlib
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import unittest.mock

import xattr

import sneakersync

import test_synchronize_base

class TestRsync(test_synchronize_base.TestSynchronizeBase):
    def test_equal(self):
        
        self._synchronize()
        self._check_synchronized()
    
    def test_add(self):
        with (self.drives[0] / "module_1" / "new").open("w") as fd:
            fd.write("new file")
        
        self._synchronize()
        self._check_synchronized()
    
    def test_remove(self):
        (self.drives[0] / "module_1" / "foo.1").unlink()
        
        self._synchronize()
        self._check_synchronized()
    
    def test_modify(self):
        with (self.drives[0] / "module_1" / "foo.1").open("w") as fd:
            fd.write("Modified file")
        
        self._synchronize()
        self._check_synchronized()
    
    def test_atime(self):
        subprocess.check_call([
            "touch", "-a", "-t", "2001" "02" "03" "23" "24" ".25",
            self.drives[0] / "module_1" / "foo.1"])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_mtime(self):
        # NOTE: if time is in the past, st_birthtime will be affected too.
        subprocess.check_call([
            "touch", "-m", "-t", "2999" "02" "03" "23" "24" ".25",
            self.drives[0] / "module_1" / "foo.1"])
        
        self._synchronize()
        self._check_synchronized()
    
    # NOTE: birthtime cannot be changed
    def test_add_birthtime(self):
        with (self.drives[0] / "module_1" / "new").open("w") as fd:
            fd.write("new file")
        # NOTE: if time is in the past, st_birthtime will be affected too.
        subprocess.check_call([
            "touch", "-ma", "-t", "2999" "02" "03" "23" "24" ".25",
            self.drives[0] / "module_1" / "new"])
        
        time.sleep(1.1)
        
        with (self.drives[1] / "module_1" / "new").open("w") as fd:
            fd.write("new file")
        # NOTE: if time is in the past, st_birthtime will be affected too.
        subprocess.check_call([
            "touch", "-ma", "-t", "2999" "02" "03" "23" "24" ".25",
            self.drives[1] / "module_1" / "new"])
        
        self.assertNotEqual(
            (self.drives[0] / "module_1" / "new").stat().st_birthtime,
            (self.drives[1] / "module_1" / "new").stat().st_birthtime)
        
        self._synchronize()
        self._check_synchronized()
    
    # NOTE: ctime is not preserved
    
    def test_mode(self):
        (self.drives[0] / "module_1" / "foo.1").chmod(0o432)
        
        self._synchronize()
        self._check_synchronized()
    
    def test_acl(self):
        subprocess.check_call([
            "chmod", "+a", "group:everyone deny execute",
            self.drives[0] / "module_1" / "foo.1"])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_xattr(self):
        subprocess.check_call([
            "xattr", "-w", "new_attribute", "new_value",
            self.drives[0] / "module_1" / "foo.1"])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_flags(self):
        subprocess.check_call([
            "chflags", "opaque", self.drives[0] / "module_1" / "foo.1"])
        
        self._synchronize()
        self._check_synchronized()
    
    def _synchronize(self):
        with unittest.mock.patch("socket.gethostname", lambda: "first.host"):
            configuration = sneakersync.operations.read_configuration(
                self.sneakerdrive / "sneakersync.cfg")
            state = sneakersync.State.load(self.sneakerdrive / "sneakersync.dat")
            
            # On first computer
            for module in configuration["modules"]:
                sneakersync.rsync.send(
                    self.sneakerdrive, configuration, module, state)
            
            state.previous_direction = "send"
            state.previous_date = datetime.datetime.now()
            state.previous_host = socket.gethostname()
            state.save()
        
        time.sleep(1.1)
        
        with unittest.mock.patch("socket.gethostname", lambda: "second.host"):
            configuration = sneakersync.operations.read_configuration(
                self.sneakerdrive / "sneakersync.cfg")
            state = sneakersync.State.load(self.sneakerdrive / "sneakersync.dat")
            
            # On second computer
            state = sneakersync.State.load(self.sneakerdrive / "sneakersync.dat")
            for module in configuration["modules"]:
                sneakersync.rsync.receive(
                    self.sneakerdrive, configuration, module, state)
    
if __name__ == "__main__":
    unittest.main()
