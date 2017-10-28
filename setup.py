from codecs import open
import glob
import os

from setuptools import setup, find_packages

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "README"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="sneakersync",
    version="1.1.2",
    
    description="Synchronize files through the sneakernet",
    long_description=long_description,
    
    url="https://github.com/lamyj/sneakersync",
    
    author="Julien Lamy",
    author_email="julien@seasofcheese.net",
    
    license="MIT",
    
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        
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
    
    keywords="synchronization, removable drive, sneakernet, rsync",

    packages=find_packages(),
    include_package_data=True,
    install_requires=["pyyaml", "six"],
    
    entry_points={ "console_scripts": [ "sneakersync=sneakersync.main:main"] },
)
