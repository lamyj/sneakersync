import os
import shutil
import subprocess
import stat
import tempfile
import unittest

import xattr

import sneakersync

class TestSend(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.local = None
        self.sneakerdrive = None
    
    def setUp(self):
        # WARNING: don't use the default temp dir, it might behave weirdly with
        # respect to permissions
        here = os.path.abspath(os.path.dirname(__file__))
        
        self.local = tempfile.mkdtemp(dir=here)
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
                "attribute_name", "attribute_value")
            os.chmod(
                os.path.join(module_root, "subdir", "bar.{}".format(i+1)),
                0o440)
            
            with open(
                    os.path.join(module_root, "subdir", 
                    "locally_excluded.{}".format(i+1)), "w") as fd:
                fd.write("Content of locally_excluded.{}".format(i+1))
        
        self.sneakerdrive = tempfile.mkdtemp(dir=here)
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
        os.makedirs(self.local_clone)
    
    def tearDown(self):
        shutil.rmtree(self.local_clone)
        shutil.rmtree(self.sneakerdrive)
        shutil.rmtree(self.local)
    
    def test_transmit(self):
        sneakersync.send(self.sneakerdrive)
        
        for entry in os.listdir(self.local):
            os.rename(
                os.path.join(self.local, entry),
                os.path.join(self.local_clone, entry))
        
        sneakersync.receive(self.sneakerdrive)
        
        self._check()

    def _check(self):
        configuration = sneakersync.read_configuration(
            os.path.join(self.sneakerdrive, "sneakersync.cfg"))
        for module in configuration["modules"]:
            local_root = os.path.join(self.local, module["root"])
            local_clone_root = os.path.join(self.local_clone, module["root"])
            
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
                    self.assertEqual(
                        open(os.path.join(local_dirpath, name)).read(),
                        open(os.path.join(dirpath, name)).read())
            
            for dirpath, dirnames, filenames in os.walk(local_root):
                local_clone_dirpath = dirpath.replace(
                    local_root, local_clone_root)
                for name in dirnames+filenames:
                    self.assertTrue(
                        os.path.exists(
                            os.path.join(local_clone_dirpath, name)))

if __name__ == "__main__":
    unittest.main()
