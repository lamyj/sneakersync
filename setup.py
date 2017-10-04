from codecs import open
import glob
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="sneakersync",
    version="1.0.0",
    
    description="Synchronize files through the sneakernet",
    long_description=long_description,
    
    url="https://www.cabbages-and-kings.net",
    
    author="Julien Lamy",
    author_email="julien@seasofcheese.net",
    
    license="MIT",
    
    classifiers=[
        "Development Status :: 4 - Beta",
        
        "Environment :: Console",
        
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        
        "Topic :: Communications :: File Sharing",
        "Topic :: System :: Archiving :: Mirroring",
        
        "License :: OSI Approved :: MIT License",
        
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    
    keywords="synchronization, removable drive, sneakernet",

    packages=find_packages(exclude=["pyyaml"]),
    
    entry_points={ "console_scripts": [ "sneakersync=sneakersync:main"] },
)
