# Sneakersync

Synchronize files through the [sneakernet](https://en.wikipedia.org/wiki/Sneakernet), i.e. using a removable drive.

Requirements:

* [rsync](https://rsync.samba.org/). The version must support extended attributes (`-X` flag).
* A removable drive with a filesystem matching the source and target computers.
* Feet or a compatible mean of transportation of the removable drive between computers.

## Installation

Simply run `pip install sneakersync`.

## Configuration

The configuration is a [YAML](https://en.wikipedia.org/wiki/YAML)-formatted file that contains *modules* (directories to be synchronized) and *filters* (rules that exclude or include files or directories). Each module must contain a *root* entry (the top-level path to be synchronized) and may contain filters; if no filter is specified, all files and directories below the root of the module are included. Filters are defined by a list of *include* or *exclude* directives.

A minimal example which synchronizes the home folder of a user would look like:
```yaml
modules:
  - root: /home/john.doe
```

To exclude a directory (and its content) and files with a given extension from a module, add a *filters* directive:
```yaml
modules:
  - root: /home/john.doe
    filters:
      - exclude: /home/john.doe/.firefox/caches
      - exclude: *.pyc
```

To filter entries from all modules, use the top-level *filters* directive:
```yaml
modules:
  - root: /home/john.doe
  - root: /home/jane.blogs
filters:
  - exclude: .firefox/caches
```

Filters defined at the top-level will have priority over module-level filters.

Each module can have a host-specific root, e.g. if your username differs between computers, with the following syntax:

```yaml
modules:
  - root: 
      first.host: /home/john.doe
      second.host: /home/john
```

If host-specific roots are used, sending or receiving using an undeclared host will cause an error.

## Usage

1. Create a filesystem on a removable drive that matches the source and target computers. 
2. Optional, but highly recommended: [encrypt](https://en.wikipedia.org/wiki/Disk_encryption) your removable drive.
3. Store the [configuration](#configuration) in a file named `sneakersync.cfg` on the root of the drive.
4. To send data, run `sneakersync send <PATH_TO_YOUR_DRIVE>`.
5. Move your drive to the other computer and plug it in.
6. To receive data, run `sneakersync receive <PATH_TO_YOUR_DRIVE>`.

Known limitations:
* The last access time (`atime`) is not preserved: rsync needs to access files in order to transfer them.
* The creation / meta-data change time (`ctime`) is not preserved: this attribute is not user-modifiable.
