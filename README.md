# Sneakersync

Synchronize files through the [sneakernet](https://en.wikipedia.org/wiki/Sneakernet), i.e. using a removable drive.

Requirements:
* [rsync](https://rsync.samba.org/). The version must support extended attributes (`-X` flag).
* A removable drive with a filesystem matching the source and target computers.
* Feet or a compatible mean of transportation of the removable drive between computers.
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
