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

class TestRsync(unittest.TestCase):
    def setUp(self):
        if "SNEAKERSYNC_ROOT" not in os.environ:
            raise Exception("SNEAKERSYNC_ROOT not defined")
        if not os.path.isdir(os.environ["SNEAKERSYNC_ROOT"]):
            raise Exception("SNEAKERSYNC_ROOT is not a directory")
        
        # Create the two hard drives and the sneakerdrive
        self.root = pathlib.Path(tempfile.mkdtemp(dir=os.environ["SNEAKERSYNC_ROOT"]))
        self.drives = [self.root / "drive_1", self.root / "drive_2"]
        self.sneakerdrive = self.root / "sneakerdrive"
        for drive in self.drives+[self.sneakerdrive]:
            drive.mkdir()
        
        # The "current" hard drive: do not create the directory since it will
        # correspond to either drive_1 or drive_2
        self.drive = self.root / "drive"
        
        # Sneakersync configuration:
        with (self.sneakerdrive / "sneakersync.cfg").open("w") as fd:
            fd.write("\n".join([
                "modules:",
                "  - root: {}/module_1".format(self.drive),
                "    filters: ",
                "      - exclude: locally_excluded.1",
                # WARNING: module_2 is skipped
                "  - root: {}/module_3".format(self.drive),
                "    filters: ",
                "      - exclude: locally_excluded.3",
                "filters: ",
                "  - exclude: globally_excluded.*"
            ]))
        self.excluded = [
            "module_1/subdir/locally_excluded.1",
            "module_2",
            "module_2/*",
            "module_3/subdir/locally_excluded.3",
            "*/globally_excluded.*"
        ]
        
        # Create the test data
        self.drives[0].rename(self.drive)
        for i in range(3):
            module_root = self.drive / "module_{}".format(1+i)
            module_root.mkdir()
            
            with (module_root / "foo.{}".format(i+1)).open("w") as fd:
                fd.write("Content of foo.{}".format(i+1))
            
            with (module_root / "globally_excluded.{}".format(i+1)).open("w") as fd:
                fd.write("Content of globally_excluded.{}".format(i+1))
            
            (module_root / "subdir").mkdir()
            with (module_root / "subdir" / "bar.{}".format(i+1)).open("w") as fd:
                fd.write("Content of bar.{}".format(i+1))
            xattr.setxattr(
                module_root / "subdir" / "bar.{}".format(i+1),
                b"attribute_name", b"attribute_value")
            (module_root / "subdir" / "bar.{}".format(i+1)).chmod(0o402)
            subprocess.call([
                "chmod", "+a", "group:everyone allow delete", 
                module_root / "subdir" / "bar.{}".format(i+1)])
            
            with (module_root / "subdir" / "locally_excluded.{}".format(i+1)).open("w") as fd:
                fd.write("Content of locally_excluded.{}".format(i+1))
        self.drive.rename(self.drives[0])
        
        time.sleep(1.1)
        subprocess.check_call([
            "rsync", "-aHAXN", "--fileflags",
            "{}/".format(self.drives[0]), "{}/".format(self.drives[1])])
        
        self.drives[1].rename(self.drive)
        for i in [0, 2]:
            module_root = self.drive / "module_{}".format(1+i)
            with (module_root / "globally_excluded.{}".format(i+1)).open("w") as fd:
                fd.write("Modified content of globally_excluded.{}".format(i+1))
            with (module_root / "subdir" / "locally_excluded.{}".format(i+1)).open("w") as fd:
                fd.write("Modified content of locally_excluded.{}".format(i+1))
        for dirpath, dirnames, filenames in os.walk(self.drive / "module_2"):
            for filename in filenames:
                path = pathlib.Path(dirpath, filename)
                path.chmod(0o600)
                with path.open("w") as fd:
                    fd.write("Modified content of {}".format(filename))
        self.drive.rename(self.drives[1])
    
    def tearDown(self):
        # WARNING: output of chmod is silenced
        process = subprocess.Popen(
            ["chmod", "-R", "-a", "group:everyone deny delete", self.root],
            stderr=subprocess.PIPE)
        process.communicate()
        shutil.rmtree(self.root)
    
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
        
        # On second computer
        self.drives[1].rename(self.drive)
        for module in configuration["modules"]:
            sneakersync.rsync.receive(self.sneakerdrive, configuration, module)
        self.drive.rename(self.drives[1])
    
    def _check_synchronized(self):
        for dirpath, dirnames, filenames in os.walk(self.drives[0]):
            dirpath_1 = pathlib.Path(dirpath)
            dirpath_2 = self.drives[1] / dirpath_1.relative_to(self.drives[0])
            entries = [(dirpath_1/x, dirpath_2/x) for x in dirnames+filenames]
            
            for entry_1, entry_2 in entries:
                if not self._is_excluded(entry_1, self.drives[0]):
                    stat_1 = entry_1.stat()
                    stat_2 = entry_2.stat()
                    self.assertEqual(
                        stat_1.st_mode, stat_2.st_mode, 
                        "(0o{:o} != 0o{:o})".format(
                            stat_1.st_mode, stat_2.st_mode))
                    self.assertEqual(stat_1.st_uid, stat_2.st_uid)
                    self.assertEqual(stat_1.st_gid, stat_2.st_gid)
                    self.assertEqual(stat_1.st_atime, stat_2.st_atime)
                    self.assertEqual(stat_1.st_birthtime, stat_2.st_birthtime)
                    self.assertEqual(stat_1.st_mtime, stat_2.st_mtime)
                    # WARNING ctime will NOT be kept
                    self.assertEqual(stat_1.st_flags, stat_2.st_flags)
                    
                    xattrs_1 = [
                        (x, xattr.getxattr(entry_1, x)) 
                        for x in sorted(xattr.listxattr(entry_1))]
                    xattrs_2 = [
                        (x, xattr.getxattr(entry_2, x)) 
                        for x in sorted(xattr.listxattr(entry_2))]
                    self.assertSequenceEqual(xattrs_1, xattrs_2)
                    
                    acls = [
                        subprocess.check_output(
                            ["ls", "-lde", x]).splitlines()[1:]
                        for x in [entry_1, entry_2]]
                    self.assertEqual(*acls)
                
                for name in filenames:
                    path_1 = dirpath_1 / name
                    path_2 = dirpath_2 / name
                    
                    if self._is_excluded(path_1, self.drives[0]):
                        test = self.assertNotEqual
                    else:
                        test = self.assertEqual
                    with path_1.open() as fd_1, path_2.open() as fd_2:
                        test(fd_1.read(), fd_2.read())
        
        for dirpath, dirnames, filenames in os.walk(self.drives[1]):
            dirpath_1 = pathlib.Path(dirpath)
            dirpath_2 = self.drives[0] / dirpath_1.relative_to(self.drives[1])
            for name in dirnames+filenames:
                path = dirpath_2 / name
                if self._is_excluded(path, self.drives[0]):
                    continue
                # Content and flags have been checked
                self.assertTrue(path.exists())
    
    def _is_excluded(self, path, root):
        excluded = any(
            fnmatch.fnmatch(path.relative_to(root), x) for x in self.excluded)
        return excluded

if __name__ == "__main__":
    unittest.main()
