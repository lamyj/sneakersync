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

def call_subprocess(command, action, module):
    """Call a command, redirect output given current logging level."""
    
    output = []
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(process.stdout.readline, ""):
        output.append(line)
        if sneakersync.logger.getEffectiveLevel() <= logging.INFO:
            sys.stdout.write(line)
    process.poll()
    if process.returncode != 0:
        raise sneakersync.Exception(action, module, "".join(output))
