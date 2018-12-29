import fnmatch
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import unittest

import xattr

import sneakersync

import test_synchronize_base

class TestRsync(test_synchronize_base.TestSynchronizeBase):
    def test_equal(self):
        self._synchronize()
        self._check_synchronized()
    
    def test_add(self):
        self.drives[0].rename(self.drive)
        with (self.drive / "module_1" / "new").open("w") as fd:
            fd.write("new file")
        self.drive.rename(self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_remove(self):
        self.drives[0].rename(self.drive)
        (self.drive / "module_1" / "foo.1").unlink()
        self.drive.rename(self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_modify(self):
        self.drives[0].rename(self.drive)
        with (self.drive / "module_1" / "foo.1").open("w") as fd:
            fd.write("Modified file")
        self.drive.rename(self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_atime(self):
        self.drives[0].rename(self.drive)
        subprocess.check_call([
            "touch", "-a", "-t", "2001" "02" "03" "23" "24" ".25",
            self.drive / "module_1" / "foo.1"])
        self.drive.rename(self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_mtime(self):
        self.drives[0].rename(self.drive)
        subprocess.check_call([
            "touch", "-m", "-t", "2001" "02" "03" "23" "24" ".25",
            self.drive / "module_1" / "foo.1"])
        self.drive.rename(self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    # NOTE: birthtime cannot be changed
    
    # NOTE: ctime is not preserved
    
    def test_mode(self):
        self.drives[0].rename(self.drive)
        (self.drive / "module_1" / "foo.1").chmod(0o432)
        self.drive.rename(self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_acl(self):
        self.drives[0].rename(self.drive)
        subprocess.check_call([
            "chmod", "+a", "group:everyone deny execute",
            self.drive / "module_1" / "foo.1"])
        self.drive.rename(self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_xattr(self):
        self.drives[0].rename(self.drive)
        subprocess.check_call([
            "xattr", "-w", "new_attribute", "new_value",
            self.drive / "module_1" / "foo.1"])
        self.drive.rename(self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_flags(self):
        self.drives[0].rename(self.drive)
        subprocess.check_call([
            "chflags", "opaque",
            self.drive / "module_1" / "foo.1"])
        self.drive.rename(self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def _synchronize(self):
        configuration = sneakersync.operations.read_configuration(
            self.sneakerdrive / "sneakersync.cfg")
        
        # On first computer
        self.drives[0].rename(self.drive)
        for module in configuration["modules"]:
            sneakersync.rsync.send(self.sneakerdrive, configuration, module)
        self.drive.rename(self.drives[0])
        
        time.sleep(1.1)
        
        # On second computer
        self.drives[1].rename(self.drive)
        for module in configuration["modules"]:
            sneakersync.rsync.receive(self.sneakerdrive, configuration, module)
        self.drive.rename(self.drives[1])
    
if __name__ == "__main__":
    unittest.main()
