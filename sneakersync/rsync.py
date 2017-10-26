import logging
import subprocess
import sys

sneakersync = sys.modules["sneakersync"]

def get_filters(filters):
    """Return the rsync options for the given filters."""
    
    arguments = []
    for filter_ in filters:
        if len(filter_) > 1:
            raise Exception(
                "Filter must contain only one entry: {}".format(filter_))
        if "exclude" in filter_:
            arguments += ["--exclude", filter_["exclude"]]
        elif "include" in filter_:
            arguments += ["--include", filter_["include"]]
        else:
            raise Exception(
                "Filter must contain include or exclude: {}".format(filter_))
    return arguments

def get_verbosity_options(progress):
    options = []
    if progress:
        options.append("--progress")
    if sneakersync.logger.getEffectiveLevel() <= logging.INFO:
        options.append("--stats")
    if sneakersync.logger.getEffectiveLevel() <= logging.DEBUG:
        options.extend(["--verbose", "--verbose"])
    return options

def call_subprocess(command, action, module):
    """Call a command, redirect output given current logging level."""
    
    output = []
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(process.stdout.readline, b""):
        output.append(line)
        encoding = (
            getattr(sys.stdout, "encoding", None)
            or getattr(sys.stdin, "encoding", None)
            or "utf-8"
        )
        sys.stdout.write(line.decode(encoding))
    
    process.wait()
    process.stdout.close()
    if process.returncode != 0:
        raise sneakersync.Exception(action, module, "".join(output))
