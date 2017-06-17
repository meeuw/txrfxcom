#!/usr/bin/env python

from twisted.internet import protocol
from twisted.internet import task

import struct
import yaml
import glob
import os.path
import pkg_resources


class RFXCOM(protocol.Protocol):
    def __init__(self):
        self.testTransportLoop = task.LoopingCall(self.testTransport)
        self.testTransportLoop.start(1.0)  # call every second
        self.protocols = {}
        for fileName in pkg_resources.resource_listdir("txrfxcom", 'protocol'):
            with pkg_resources.resource_stream("txrfxcom",
                                               "protocol/" + fileName) as f:
                proto = yaml.load(f)
                protoName = os.path.basename(fileName)[:-4]
                self.protocols[proto['value']] = protoName
        self.recvBuf = b''
        self.recvState = 'IDLE'

    def testTransport(self):
        if (self.transport):
            self.testTransportLoop.stop()
            readyTransport = getattr(self, 'readyTransport', None)
            if (callable(readyTransport)):
                readyTransport()

    def fields(self, p, **args):
        result = []

        flags = []
        enums = p["enums"]
        for v in p['fields']:
            if v.startswith('f'):
                flags.append(args[v] << len(flags))
                if len(flags) >= 8:
                    result.append(sum(flags))
                    flags = []
            elif v.startswith('e'):
                idx = '[eSubtype]'
                if v.endswith(idx):
                    v = v[:-len(idx)]
                    result.append(enums[v][args["eSubtype"]][args[v]])
                else:
                    result.append(enums[v][args[v]])
            else:
                result.append(args[v])
        return result

    @staticmethod
    def packfmt(fields):
        i = 0
        flags = 0
        for field in fields:
            if field[0] == 'f':
                if (flags % 8) == 0:
                    i += 1
                flags += 1
            else:
                i += 1

        return i * 'B'

    def generate(self, **args):
        with pkg_resources.resource_stream(
                "txrfxcom", 'protocol/{0}.yml'.format(args['type'])) as f:
            p = yaml.load(f)

        fields = [p['value']]

        fields += self.fields(p, **args)

        return struct.pack('B' + self.packfmt(['type'] + p['fields']),
                           *([len(fields)] + fields))

    @staticmethod
    def byvalue(d, value):
        for k, v in d.items():
            if v == value:
                return k

    def dataReceived(self, data):
        self.recvBuf += data
        pktlen = struct.unpack('B', self.recvBuf[0])[0]
        if len(self.recvBuf) >= pktlen:
            pkt = self.recvBuf[:pktlen + 1]
            self.recvBuf = self.recvBuf[pktlen + 1:]
            protocol = self.protocols[struct.unpack('B', pkt[1])[0]]
            with pkg_resources.resource_stream(
                    "txrfxcom", "protocol/{0}.yml".format(protocol)) as f:
                p = yaml.load(f)

            parser = getattr(self, "parse" + protocol, None)
            if callable(parser):
                args = {}
                flag = 0
                values = struct.unpack(self.packfmt(p['fields']), pkt[2:])
                for i, field in enumerate(p['fields']):
                    value = values[i-flag]
                    if field[0] == 'e':
                        value = self.byvalue(p['enums'][field], value)
                    elif field[0] == 'f':
                        value = (values[i - flag] >> flag) == 1
                        flag += 1

                    args[field] = value
                parser(**args)
            else:
                print("unhandled parse{0}({1})".format(protocol, ", ".join(
                    p['fields'])))


if __name__ == '__main__':
    #print (RFXCOM.packfmt(['cSeqnbr', 'cCmnd', 'eSubtype', 'eTranceivertype', 'cFirmwareVersion', 'fAEBlyss', 'fRubicson', 'fFineOffsetViking', 'fLighting4', 'fRSL', 'fByronSX', 'fRFU', 'fUndecoded', 'fMertik', 'fADLightwaveRF', 'fHidekiUPM', 'fLaCrosse', 'fFS20', 'fProGuard', 'fBlindsT0', 'fBlindsT1T2T3T4', 'fX10', 'fARC', 'fAC', 'fHomeEasyEU', 'fMeiantech', 'fOregonScientific', 'fATI', 'fVisonic', 'cMsg1', 'cMsg2', 'cMsg3', 'cMsg4']))
    r = RFXCOM()
    d = r.generate(
        type='InterfaceControl',
        eSubtype='Interface Control',
        cSeqnbr=0,
        eCmnd="reset",
        dummy1=1,
        dummy2=2,
        dummy3=3,
        dummy4=4,
        dummy5=5,
        dummy6=6,
        dummy7=7,
        dummy8=8,
        dummy9=9,
        dummy10=10, )
    r.dataReceived(d)
