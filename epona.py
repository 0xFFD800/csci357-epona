#!/usr/bin/env python3

from blockingdict import BlockingDict
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
from physical import Adapter, MultiportNode, BROADCAST_MAC, MARE_PROTONUM


class EponaAdapter(Adapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any initialization you need below this line

    def output(self, protonum, dst, dgram):
        """
        Called when the network layer wishes to transmit a datagram to a
        destination host.  Provides the protocol number, destination MAC
        address, and datagram contents as bytes.
        """

    def rx(self, frame):
        """
        Called when a frame arrives at the adapter.  Provides the frame
        contents as bytes.
        """
        pass

    def output_ip(self, protonum, addr, dgram):
        """
        Called when the network layer wishes to transmit a datagram to a
        destination host.  Provides the protocol number, destination IPv4
        address as four bytes, and datagram contents as bytes.
        """
        pass


class EponaSwitch(MultiportNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any initialization you need below this line

    def rx(self, port, frame):
        """
        Called when a frame arrives at any port.  Provides the port number as
        an int and the frame contents as bytes.
        """
        pass
