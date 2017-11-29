"""Test RFlink serial low level and packet parsing protocol."""

from unittest.mock import Mock

import pytest

from rflink.protocol import PacketHandling

COMPLETE_PACKET = b'20;E0;NewKaku;ID=cac142;SWITCH=1;CMD=ALLOFF;\r\n'
INCOMPLETE_PART1 = b'20;E0;NewKaku;ID=cac'
INCOMPLETE_PART2 = b'142;SWITCH=1;CMD=ALLOFF;\r\n'

# Testing parsing of 4 structures
"""
COMMAND_TEMPLATES = {
'minimal': '{node};{<protocol>};{<id>};',
'command': '{node};{<protocol>};{<id>};{<command>};',
'switch_command': '{node};{<protocol>};{<id>};{<switch>};{<command>};',
'switch_value_command': '{node};{<protocol>};{<id>};{<switch>};{<value>};{<command>};'
}
"""


COMPLETE_PACKET_DICT = {
    'id': 'cac142',
    'node': 'gateway',
    'protocol': 'newkaku',
    'command': 'alloff',
    'switch': '1',
}


PACKET_MINIMAL=b'10;DELTRONIC;001c33;\r\n'
PACKET_COMMAND=b'10;MERTIK;64;UP;\r\n'
PACKET_SWITCH_COMMAND=b'10;NewKaku;0cac142;3;ON;\r\n'
PACKET_SWITCH_VALUE_COMMAND=b'10;MiLightv1;F746;00;3c00;ON;\r\n'

PACKET_MINIMAL_DICT = {
    'id': '001c33',
    'node': 'gateway',
    'protocol': 'deltronic',
}


PACKET_COMMAND_DICT = {
    'id': '64',
    'node': 'gateway',
    'protocol': 'mertik',
    'command': 'up',
}

PACKET_SWITCH_COMMAND_DICT = {
    'id': '0cac142',
    'node': 'gateway',
    'protocol': 'newkaku',
    'command': 'on',
    'switch': '3',
}

PACKET_SWITCH_VALUE_COMMAND_DICT = {
    'id': 'F746',
    'node': 'gateway',
    'protocol': 'milightv1',
    'command': 'on',
    'switch': '00',
    'value': '3c00',
}

@pytest.fixture
def protocol(monkeypatch):
    """Rflinkprotocol instance with mocked handle_packet."""
    monkeypatch.setattr(PacketHandling, 'handle_packet', Mock())
    return PacketHandling(None)


def test_complete_packet(protocol):
    """Protocol should parse and output complete incoming packets."""
    protocol.data_received(COMPLETE_PACKET)

    protocol.handle_packet.assert_called_once_with(COMPLETE_PACKET_DICT)

def test_p1(protocol):
    protocol.data_received(PACKET_MINIMAL)
    protocol.handle_packet.assert_called_once_with(PACKET_MINIMAL_DICT)

def test_p2(protocol):
    protocol.data_received(PACKET_COMMAND)
    protocol.handle_packet.assert_called_once_with(PACKET_COMMAND_DICT)

def test_p3(protocol):
    protocol.data_received(PACKET_SWITCH_COMMAND)
    protocol.handle_packet.assert_called_once_with(PACKET_SWITCH_COMMAND_DICT)

def test_p4(protocol):
    protocol.data_received(PACKET_SWITCH_VALUE_COMMAND)
    protocol.handle_packet.assert_called_once_with(PACKET_SWITCH_VALUE_COMMAND_DICT)


def test_split_packet(protocol):
    """Packet should be allowed to arrive in pieces."""
    protocol.data_received(INCOMPLETE_PART1)
    protocol.data_received(INCOMPLETE_PART2)

    protocol.handle_packet.assert_called_once_with(COMPLETE_PACKET_DICT)


def test_starting_incomplete(protocol):
    """An initial incomplete packet should be discarded."""
    protocol.data_received(INCOMPLETE_PART2)
    protocol.data_received(INCOMPLETE_PART1)
    protocol.data_received(INCOMPLETE_PART2)

    protocol.handle_packet.assert_called_once_with(COMPLETE_PACKET_DICT)


def test_multiple_packets(protocol):
    """Multiple packets should be parsed."""
    protocol.data_received(COMPLETE_PACKET)
    protocol.data_received(COMPLETE_PACKET)

    assert protocol.handle_packet.call_count == 2
    protocol.handle_packet.assert_called_with(COMPLETE_PACKET_DICT)
