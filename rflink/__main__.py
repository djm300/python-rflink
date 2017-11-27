"""Command line interface for rflink library.

Usage:
  rflink [-v | -vv] [options]
  rflink [-v | -vv] [options] [--repeat <repeat>] (on,off,allon,alloff,up,down,stop,disco+,disco-,mode0,mode1,mode2,mode3,mode4,mode5,mode6,mode7,mode8,pair,unpair,bright,color) <id> <switch> <value>
  rflink (-h | --help)
  rflink --version

Options:
  -p --port=<port>   Serial port to connect to [default: /dev/ttyACM0],
                       or TCP port in TCP mode.
  --baud=<baud>      Serial baud rate [default: 57600].
  --host=<host>      TCP mode, connect to host instead of serial port.
  --repeat=<repeat>  How often to repeat a command [default: 1].
  -m=<handling>      How to handle incoming packets [default: event].
  --ignore=<ignore>  List of device ids to ignore, end with * to match wildcard.
  -h --help          Show this screen.
  -v                 Increase verbosity
  --version          Show version.
"""

import asyncio
import logging
import sys

import pkg_resources
from docopt import docopt

from .protocol import (
    EventHandling,
    InverterProtocol,
    PacketHandling,
    RepeaterProtocol,
    RflinkProtocol,
    create_rflink_connection
)

PROTOCOLS = {
    'command': RflinkProtocol,
    'event': EventHandling,
    'print': PacketHandling,
    'invert': InverterProtocol,
    'repeat': RepeaterProtocol,
}

# Defines the values this tool will accept as <command>
ALL_COMMANDS = ['on', 'off', 'allon', 'alloff', 'up', 'down', 'stop', 'disco+', 'disco-', 'mode0', 'mode1', 'mode2', 'mode3','mode4','mode5','mode6','mode7','mode8','pair','unpair','bright','color']


"""
Defines the presence and structure of parameters in the command we will send to RFLink

'minimal': '{node};{protocol};{id};',
'command': '{node};{protocol};{id};{command};',
'switch_command': '{node};{protocol};{id};{switch};{command};',
'switch_value_command': '{node};{protocol};{id};{switch};{value};{command};'
"""
from .parser import COMMAND_TEMPLATES 


def main(argv=sys.argv[1:], loop=None):
    """Parse argument and setup main program loop."""
    args = docopt(__doc__, argv=argv,
                  version=pkg_resources.require('rflink')[0].version)

    level = logging.ERROR
    if args['-v']:
        level = logging.INFO
    if args['-v'] == 2:
        level = logging.DEBUG
    logging.basicConfig(level=level)

    if not loop:
        loop = asyncio.get_event_loop()

    if args['--ignore']:
        ignore = args['--ignore'].split(',')
    else:
        ignore = []

    command = next((c for c in ALL_COMMANDS if args[c] is True), None)

    if command:
        # Valid command keyword was found and we assume this is a command
        protocol = PROTOCOLS['command']
    else:
        # It's not a command: event, print, invert, repeat
        protocol = PROTOCOLS[args['-m']]
    conn = create_rflink_connection(
        protocol=protocol,
        host=args['--host'],
        port=args['--port'],
        baud=args['--baud'],
        loop=loop,
        ignore=ignore,
    )

    transport, protocol = loop.run_until_complete(conn)

    try:
        if command:
            # device_id is no longer sufficient for containing all the command info. We replace the string device_id by a dict which contains all provided parameters, including a 'type' key indicating the structure the packet should have on the wire to the RFLink.
            # TODO: construct dict of arguments command, switch, id, type
            
            # now that we prepared the dict, let's pass it on.
            for _ in range(int(args['--repeat'])):
                loop.run_until_complete(
                    protocol.send_command_ack(
                        args['<id>'], command))
        else:
            loop.run_forever()
    except KeyboardInterrupt:
        # cleanup connection
        transport.close()
        loop.run_forever()
    finally:
        loop.close()
