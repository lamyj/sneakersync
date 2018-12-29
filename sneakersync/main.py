import argparse
import logging
import pathlib
import sys

import sneakersync

def main():
    parser = argparse.ArgumentParser(
        description="Send and receive files through the sneakernet")
    parser.add_argument(
        "--verbosity", "-v",
        choices=["error", "warning", "info", "debug"], default="warning")
    
    backend = sneakersync.rsync
    
    progress_group = parser.add_mutually_exclusive_group()
    progress_group.add_argument(
        "--progress", action="store_true", help="Display progress bar")
    
    subparsers = parser.add_subparsers(help="Sub-commands help")
    
    send_parser = subparsers.add_parser(
        "send", help="Send data on the sneakernet",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    send_parser.add_argument("destination", type=pathlib.Path)
    send_parser.set_defaults(
        function=lambda destination, progress: sneakersync.operations.send(destination, progress, backend))
    
    receive_parser = subparsers.add_parser(
        "receive", help="Receive data from the sneakernet",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    receive_parser.add_argument("source", type=pathlib.Path)
    receive_parser.set_defaults(
        function=lambda source, progress: sneakersync.operations.receive(source, progress, backend))
    
    arguments = vars(parser.parse_args())
    
    verbosity = arguments.pop("verbosity")
    logging.basicConfig(
        level=verbosity.upper(), 
        format="%(levelname)s: %(message)s")
    
    if "function" not in arguments:
        parser.error("No action specified")    
    function = arguments.pop("function")
    
    try:
        function(**arguments)
    except sneakersync.Exception as e:
        sneakersync.logger.error(
            "Could not {} module {}: \n{}".format(
                e.action, e.module["root"], e.text))
        if sneakersync.logger.getEffectiveLevel() <= logging.DEBUG:
            raise
    except Exception as e:
        sneakersync.logger.error(e)
        if sneakersync.logger.getEffectiveLevel() <= logging.DEBUG:
            raise
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
