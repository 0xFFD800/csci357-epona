#!/usr/bin/env python3

from blockingdict import BlockingDict
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
from physical import Adapter, MultiportNode, BROADCAST_MAC, MARE_PROTONUM

def calc_checksum(frame) :
    return sum([ int.from_bytes(frame[i:i+2], byteorder="big") for i in range(0, len(frame), 2) ]) & 0xFFFF

def assemble_frame(src, dst, protonum, dgram) :
    frame = src + dst + protonum.to_bytes(2, byteorder="big") + dgram
    return frame + calc_checksum(frame).to_bytes(2, byteorder="big")

def disassemble_frame(frame) :
    return (frame[:6], frame[6:12], int.from_bytes(frame[12:14], byteorder="big"), frame[14:-2], int.from_bytes(frame[-2:], byteorder="big"))

def assemble_mare(mode, srcip, dstip) :
    return (0 if mode == 'rqst' else 1).to_bytes(1, byteorder="big") + srcip.packed + dstip.packed

def disassemble_mare(dgram) :
    return ('rqst' if dgram[0] == 0 else 'resp', IPv4Address(dgram[1:5]), IPv4Address(dgram[5:9]))

class EponaAdapter(Adapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mare_table = BlockingDict()

    def output(self, protonum, dst, dgram):
        self.tx(assemble_frame(self.hwaddr, dst, protonum, dgram))

    def rx(self, frame):
        src, dst, protonum, dgram, checksum = disassemble_frame(frame)
        if dst in (self.hwaddr, BROADCAST_MAC) and checksum == calc_checksum(frame[:-2]) :
            if protonum == MARE_PROTONUM :
                mode, srcip, dstip = disassemble_mare(dgram)
                if dstip == self.iface.ip :
                    match mode :
                        case 'rqst' :
                            self.output(MARE_PROTONUM, src, assemble_mare('resp', self.iface.ip, srcip))
                        case 'resp' :
                            self.mare_table[srcip.packed] = src
            else :
                self.input(protonum, dgram)

    def output_ip(self, protonum, addr, dgram) :
        a = addr if self.iface.network.overlaps(IPv4Network( (addr, 32) )) else self.gateway.packed
        if self.mare_table.get(a, timeout=0) == None :
            i = 0
            while True :
                self.output(MARE_PROTONUM, BROADCAST_MAC, assemble_mare('rqst', self.iface.ip, IPv4Address(a)))
                if self.mare_table.get(a, timeout=0.1) != None :
                    break;
                if (i := i + 1) > 2 :
                    raise self.NoRouteToHost()
        self.output(protonum, self.mare_table[a], dgram)


class EponaSwitch(MultiportNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.switch_table = {}

    def rx(self, port, frame):
        src, dst, protonum, dgram, checksum = disassemble_frame(frame)
        if checksum == calc_checksum(frame[:-2]) :
            ports = []
            if dst in self.switch_table :
                ports = [ self.switch_table[dst] ]
            else :
                ports = [ p for p in range(self.nports) ]
            for p in filter(lambda p: p != port, ports) :
                self.forward(p, frame)
            self.switch_table[src] = port
