import fnmatch
import os
import shutil
import subprocess
import tempfile
import time
import unittest

import xattr
import yaml

import sneakersync

class TestRsync(unittest.TestCase):
    def setUp(self):
        if "SNEAKERSYNC_ROOT" not in os.environ:
            raise Exception("SNEAKERSYNC_ROOT not defined")
        if not os.path.isdir(os.environ["SNEAKERSYNC_ROOT"]):
            raise Exception("SNEAKERSYNC_ROOT is not a directory")
        
        # Create the two hard drives and the sneakerdrive
        self.root = tempfile.mkdtemp(dir=os.environ["SNEAKERSYNC_ROOT"])
        self.drives = [os.path.join(self.root, "drive_1"), os.path.join(self.root, "drive_2")]
        self.sneakerdrive = os.path.join(self.root, "sneakerdrive")
        for drive in self.drives+[self.sneakerdrive]:
            os.makedirs(drive)
        
        # The "current" hard drive: do not create the directory since it will
        # correspond to either drive_1 or drive_2
        self.drive = os.path.join(self.root, "drive")
        
        # Sneakersync configuration:
        with open(os.path.join(self.sneakerdrive, "sneakersync.cfg"), "w") as fd:
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
            "module_2/*",
            "module_3/subdir/locally_excluded.3",
            "*/globally_excluded.*"
        ]
        
        # Create the test data
        os.rename(self.drives[0], self.drive)
        for i in range(3):
            module_root = os.path.join(self.drive, "module_{}".format(1+i))
            os.makedirs(module_root)
            
            with open(os.path.join(module_root, "foo.{}".format(i+1)), "w") as fd:
                fd.write("Content of foo.{}".format(i+1))
            
            with open(
                    os.path.join(
                        module_root,
                        "globally_excluded.{}".format(i+1)), "w") as fd:
                fd.write("Content of globally_excluded.{}".format(i+1))
            
            os.makedirs(os.path.join(module_root, "subdir"))
            with open(
                    os.path.join(
                        module_root, "subdir", 
                            "bar.{}".format(i+1)), "w") as fd:
                fd.write("Content of bar.{}".format(i+1))
            xattr.setxattr(
                os.path.join(module_root, "subdir", "bar.{}".format(i+1)),
                b"attribute_name", b"attribute_value")
            os.chmod(
                os.path.join(module_root, "subdir", "bar.{}".format(i+1)),
                0o402)
            subprocess.call([
                "chmod", "+a", "group:everyone allow delete", 
                os.path.join(module_root, "subdir", "bar.{}".format(i+1))])
            
            with open(
                    os.path.join(module_root, "subdir", 
                    "locally_excluded.{}".format(i+1)), "w") as fd:
                fd.write("Content of locally_excluded.{}".format(i+1))
        os.rename(self.drive, self.drives[0])
        
        time.sleep(1.1)
        subprocess.check_call([
            "rsync", "-aHAXN", "--fileflags",
            os.path.join(self.drives[0], ""), os.path.join(self.drives[1], "")])
        
        os.rename(self.drives[1], self.drive)
        for i in [0, 2]:
            module_root = os.path.join(self.drive, "module_{}".format(1+i))
            with open(
                    os.path.join(
                        module_root,
                        "globally_excluded.{}".format(i+1)), "w") as fd:
                fd.write("Modified content of globally_excluded.{}".format(i+1))
            with open(
                    os.path.join(module_root, "subdir", 
                    "locally_excluded.{}".format(i+1)), "w") as fd:
                fd.write("Modified content of locally_excluded.{}".format(i+1))
        for dirpath, dirnames, filenames in os.walk(os.path.join(self.drive, "module_2")):
            for filename in filenames:
                mode = os.stat(os.path.join(dirpath, filename)).st_mode
                os.chmod(os.path.join(dirpath, filename), 0o600)
                with open(os.path.join(dirpath, filename), "w") as fd:
                    fd.write("Modified content of {}".format(filename))
        os.rename(self.drive, self.drives[1])
    
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
        os.rename(self.drives[0], self.drive)
        with open(os.path.join(self.drive, "module_1", "new"), "w") as fd:
            fd.write("new file")
        os.rename(self.drive, self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_remove(self):
        os.rename(self.drives[0], self.drive)
        os.remove(os.path.join(self.drive, "module_1", "foo.1"))
        os.rename(self.drive, self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_modify(self):
        os.rename(self.drives[0], self.drive)
        with open(os.path.join(self.drive, "module_1", "foo.1"), "w") as fd:
            fd.write("Modified file")
        os.rename(self.drive, self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_atime(self):
        os.rename(self.drives[0], self.drive)
        subprocess.check_call([
            "touch", "-a", "-t", "2001" "02" "03" "23" "24" ".25",
            os.path.join(self.drive, "module_1", "foo.1")])
        os.rename(self.drive, self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_mtime(self):
        os.rename(self.drives[0], self.drive)
        subprocess.check_call([
            "touch", "-m", "-t", "2001" "02" "03" "23" "24" ".25",
            os.path.join(self.drive, "module_1", "foo.1")])
        os.rename(self.drive, self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    # NOTE: birthtime cannot be changed
    
    # NOTE: ctime is not preserved
    
    def test_mode(self):
        os.rename(self.drives[0], self.drive)
        os.chmod(os.path.join(self.drive, "module_1", "foo.1"), 0o432)
        os.rename(self.drive, self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_acl(self):
        os.rename(self.drives[0], self.drive)
        subprocess.check_call([
            "chmod", "+a", "group:everyone deny execute",
            os.path.join(self.drive, "module_1", "foo.1")])
        os.rename(self.drive, self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_xattr(self):
        os.rename(self.drives[0], self.drive)
        subprocess.check_call([
            "xattr", "-w", "new_attribute", "new_value",
            os.path.join(self.drive, "module_1", "foo.1")])
        os.rename(self.drive, self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def test_flags(self):
        os.rename(self.drives[0], self.drive)
        subprocess.check_call([
            "chflags", "opaque",
            os.path.join(self.drive, "module_1", "foo.1")])
        os.rename(self.drive, self.drives[0])
        
        self._synchronize()
        self._check_synchronized()
    
    def _synchronize(self):
        with open(os.path.join(self.sneakerdrive, "sneakersync.cfg")) as fd:
            configuration = yaml.load(fd)
        
        # On first computer
        os.rename(self.drives[0], self.drive)
        for module in configuration["modules"]:
            sneakersync.rsync.send(self.sneakerdrive, configuration, module)
        os.rename(self.drive, self.drives[0])
        
        # On second computer
        os.rename(self.drives[1], self.drive)
        for module in configuration["modules"]:
            sneakersync.rsync.receive(self.sneakerdrive, configuration, module)
        os.rename(self.drive, self.drives[1])
    
    def _check_synchronized(self):
        for dirpath, dirnames, filenames in os.walk(self.drives[0]):
            entries_1 = [
                os.path.join(dirpath, entry) 
                for entry in dirnames+filenames]
            
            other_dirpath = dirpath.replace(self.drives[0], self.drives[1])
            entries_2 = [
                os.path.join(other_dirpath, entry) for entry in entries_1]
            
            for entry_1, entry_2 in zip(entries_1, entries_2):
                stat_1 = os.stat(entry_1)
                stat_2 = os.stat(entry_2)
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
                
                acls_1 = subprocess.check_output(["ls", "-lde", entry_1]).splitlines()[1:]
                acls_2 = subprocess.check_output(["ls", "-lde", entry_2]).splitlines()[1:]
                self.assertEqual(acls_1, acls_2)
                
                for name in filenames:
                    path_1 = os.path.join(dirpath, name)
                    path_2 = os.path.join(other_dirpath, name)
                    
                    if self._is_excluded(path_1, self.drives[0]):
                        test = self.assertNotEqual
                    else:
                        test = self.assertEqual
                    with open(path_1) as fd_1, open(path_2) as fd_2:
                        test(fd_1.read(), fd_2.read())
        
        for dirpath, dirnames, filenames in os.walk(self.drives[1]):
            other_dirpath = dirpath.replace(self.drives[1], self.drives[0])
            for name in dirnames+filenames:
                path = os.path.join(other_dirpath, name)
                if self._is_excluded(path, self.drives[0]):
                    continue
                # Content and flags have been checked
                self.assertTrue(os.path.exists(path))
    
    def _is_excluded(self, path, root):
        excluded = any([
            fnmatch.fnmatch(path[1+len(root):], x) for x in self.excluded])
        return excluded

if __name__ == "__main__":
    unittest.main()
