import logging
import os
import shutil
import subprocess
import stat
import tempfile
import unittest

import xattr

import sneakersync

class TestTransmit(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.local = None
        self.sneakerdrive = None
    
    def setUp(self):
        sneakersync.logger.setLevel(logging.ERROR)
        # WARNING: don't use the default temp dir, it might behave weirdly with
        # respect to permissions
        here = os.path.abspath(os.path.dirname(__file__))
        
        self.local = tempfile.mkdtemp(dir=here, suffix=".local")
        for i in range(3):
            module_root = os.path.join(self.local, "module_{}".format(1+i))
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
                0o440)
            
            with open(
                    os.path.join(module_root, "subdir", 
                    "locally_excluded.{}".format(i+1)), "w") as fd:
                fd.write("Content of locally_excluded.{}".format(i+1))
        
        self.sneakerdrive = tempfile.mkdtemp(dir=here, suffix=".sneakerdrive")
        with open(os.path.join(self.sneakerdrive, "sneakersync.cfg"), "w") as fd:
            fd.write("\n".join([
                "modules:",
                "  - root: {}/module_1".format(self.local),
                "    filters: ",
                "      - exclude: locally_excluded.1",
                # WARNING: module_2 is skipped
                "  - root: {}/module_3".format(self.local),
                "    filters: ",
                "      - exclude: locally_excluded.3",
                "filters: ",
                "  - exclude: globally_excluded.*"
            ]))
        
        self.local_clone = "{}.clone".format(self.local)
        subprocess.call([
            "rsync", "-a", "--delete", "-X", 
            os.path.join(self.local, ""), os.path.join(self.local_clone, "")])
    
    def tearDown(self):
        shutil.rmtree(self.local_clone)
        shutil.rmtree(self.sneakerdrive)
        shutil.rmtree(self.local)
    
    def test_empty(self):
        sneakersync.send(self.sneakerdrive, False)
        self._swap()
        for entry in os.listdir(self.local):
            shutil.rmtree(os.path.join(self.local, entry))
        sneakersync.receive(self.sneakerdrive, False)
        
        self._check()
    
    def test_modify_content(self):
        # Initialize sneakerdrive
        sneakersync.send(self.sneakerdrive, False)
        self._swap()
        sneakersync.receive(self.sneakerdrive, False)
        
        path = os.path.join(self.local, "module_1", "subdir", "bar.1")
        os.chmod(path, 0o640)
        with open(path, "w") as fd:
            fd.write("new content")
        os.chmod(path, 0o440)
        
        sneakersync.send(self.sneakerdrive, False)
        self._swap()
        sneakersync.receive(self.sneakerdrive, False)
        
        self._check()
    
    def test_modify_xattr(self):
        # Initialize sneakerdrive
        sneakersync.send(self.sneakerdrive, False)
        self._swap()
        sneakersync.receive(self.sneakerdrive, False)
        
        path = os.path.join(self.local, "module_1", "subdir", "bar.1")
        os.chmod(path, 0o640)
        xattr.removexattr(path, "attribute_name")
        os.chmod(path, 0o440)
        
        sneakersync.send(self.sneakerdrive, False)
        self._swap()
        sneakersync.receive(self.sneakerdrive, False)
        
        self._check()
    
    def test_transmit_modify_excluded(self):
        with open(
                os.path.join(
                    self.local, "module_1", "globally_excluded.1"), "w") as fd:
            fd.write("globally-excluded modified")
        with open(
                os.path.join(
                    self.local, "module_3", "subdir", "locally_excluded.3"), 
                "w") as fd:
            fd.write("locally-excluded modified")
        with open(
                os.path.join(
                    self.local, "module_2", "subdir", "foo.2"), "w") as fd:
            fd.write("skipped modified")
        
        sneakersync.send(self.sneakerdrive, False)
        self._swap()
        sneakersync.receive(self.sneakerdrive, False)
        
        self._check()
    
    def _swap(self):
        os.rename(self.local, self.local+".tmp")
        os.rename(self.local_clone, self.local)
        os.rename(self.local+".tmp", self.local_clone)
    
    def _check(self):
        configuration = sneakersync.read_configuration(
            os.path.join(self.sneakerdrive, "sneakersync.cfg"))
        for module in configuration["modules"]:
            local_root = module["root"]
            local_clone_root = module["root"].replace(
                self.local, self.local_clone)
            
            for dirpath, dirnames, filenames in os.walk(local_clone_root):
                local_dirpath = dirpath.replace(local_clone_root, local_root)
                for name in dirnames+filenames:
                    local_name = os.path.join(local_dirpath, name)
                    local_clone_name = os.path.join(dirpath, name)
                    
                    self.assertEqual(
                        os.stat(local_name), os.stat(local_clone_name))
                    
                    self.assertSequenceEqual(
                        [
                            [x, xattr.getxattr(local_name, x)]
                            for x in sorted(xattr.listxattr(local_name))
                        ],
                        [
                            [x, xattr.getxattr(local_clone_name, x)]
                            for x in sorted(xattr.listxattr(local_clone_name))
                        ])
                
                for name in filenames:
                    path1 = os.path.join(local_dirpath, name)
                    path2 = os.path.join(dirpath, name)
                    with open(path1) as fd1, open(path2) as fd2:
                        self.assertEqual(fd1.read(), fd2.read())
            
            for dirpath, dirnames, filenames in os.walk(local_root):
                local_clone_dirpath = dirpath.replace(
                    local_root, local_clone_root)
                for name in dirnames+filenames:
                    self.assertTrue(
                        os.path.exists(
                            os.path.join(local_clone_dirpath, name)))

if __name__ == "__main__":
    unittest.main()
