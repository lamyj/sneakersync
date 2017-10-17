import argparse
import logging
import sys

sneakersync = sys.modules["sneakersync"]

def main():
    parser = argparse.ArgumentParser(
        description="Send and receive files through the sneakernet")
    parser.add_argument(
        "--verbosity", "-v",
        choices=["warning", "info", "debug"], default="warning")
    
    subparsers = parser.add_subparsers(help="Sub-commands help")
    
    send_parser = subparsers.add_parser(
        "send", help="Send data on the sneakernet",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    send_parser.add_argument("destination")
    send_parser.set_defaults(function=sneakersync.send)
    
    receive_parser = subparsers.add_parser(
        "receive", help="Receive data from the sneakernet",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    receive_parser.add_argument("source")
    receive_parser.set_defaults(function=sneakersync.receive)
    
    arguments = vars(parser.parse_args())
    
    verbosity = arguments.pop("verbosity")
    logging.basicConfig(
        level=verbosity.upper(), 
        format="%(levelname)s: %(message)s")
        
    function = arguments.pop("function")
    
    try:
        function(**arguments)
    except sneakersync.SneakersyncException as e:
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
