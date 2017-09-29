#!/usr/bin/env python

from twisted.internet import protocol
from twisted.internet import task
from twisted.python import log

import struct
import yaml
import os.path
import pkg_resources
import json
import logging


class RFXCOM(protocol.Protocol):
    def __init__(self):
        self.testTransportLoop = task.LoopingCall(self.testTransport)
        self.testTransportLoop.start(1.0)  # call every second
        self.protocols = {}
        for fileName in pkg_resources.resource_listdir("txrfxcom", 'protocol'):
            if fileName.startswith('.'): continue
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
        log.msg('dataReceived {}'.format(data), loglevel=logging.DEBUG)
        self.recvBuf += data
        pktlen = struct.unpack('B', self.recvBuf[:1])[0]
        if len(self.recvBuf) >= pktlen:
            pkt = self.recvBuf[:pktlen + 1]
            self.recvBuf = self.recvBuf[pktlen + 1:]
            protocol = self.protocols[struct.unpack('B', pkt[1:2])[0]]
            with pkg_resources.resource_stream(
                    "txrfxcom", "protocol/{0}.yml".format(protocol)) as f:
                p = yaml.load(f)

            args = {}
            flag = 0
            fmt = self.packfmt(p['fields'])
            log.msg("{} {} {}".format(fmt, len(fmt), len(pkt)), loglevel=logging.DEBUG)

            values = struct.unpack(fmt, pkt[2:])
            i = 0
            for field in p['fields']:
                value = values[i]
                if field[0] == 'e':
                    value = self.byvalue(p['enums'][field], value)
                    i += 1
                elif field[0] == 'f':
                    value = ((values[i] >> flag) & 1) == 1
                    flag += 1
                    if flag >= 8:
                        flag = 0
                        i += 1
                else:
                    i += 1
                args[field] = value

            parser = getattr(self, "parse" + protocol, None)
            if callable(parser):
                parser(**args)
            else:
                print("unhandled parse{0}({1})".format(protocol, ", ".join(
                    p['fields'])))
                print(json.dumps(args, indent=4))


if __name__ == '__main__':
    #print (RFXCOM.packfmt(['cSeqnbr', 'cCmnd', 'eSubtype', 'eTranceivertype', 'cFirmwareVersion', 'fAEBlyss', 'fRubicson', 'fFineOffsetViking', 'fLighting4', 'fRSL', 'fByronSX', 'fRFU', 'fUndecoded', 'fMertik', 'fADLightwaveRF', 'fHidekiUPM', 'fLaCrosse', 'fFS20', 'fProGuard', 'fBlindsT0', 'fBlindsT1T2T3T4', 'fX10', 'fARC', 'fAC', 'fHomeEasyEU', 'fMeiantech', 'fOregonScientific', 'fATI', 'fVisonic', 'cMsg1', 'cMsg2', 'cMsg3', 'cMsg4']))
    class RFXTest(RFXCOM):
        def parseInterfaceControl(self, eSubtype, cSeqnbr, eCmnd, dummy1, dummy2, fAEBlyss, fRubicson, fFineOffsetViking, fLighting4, fRSL, fByronSX, fRFU, fUndecoded, fMertik, fADLightwaveRF, fHidekiUPM, fLaCrosse, fFS20, fProGuard, fBlindsT0, fBlindsT1T2T3T4, fX10, fARC, fAC, fHomeEasyEU, fMeiantech, fOregonScientific, fATI, fVisonic, fKeeLoq, fHomeConfort, fRFU2, fRFU3, fRFU4, fRFU5, fRFU6, fRFU7, dummy7, dummy8, dummy9):
            print ("parseInterfaceControl eSubtype {}, cSeqnbr {}, eCmnd {}, dummy1 {}, dummy2 {}, fAEBlyss {}, fRubicson {}, fFineOffsetViking {}, fLighting4 {}, fRSL {}, fByronSX {}, fRFU {}, fUndecoded {}, fMertik {}, fADLightwaveRF {}, fHidekiUPM {}, fLaCrosse {}, fFS20 {}, fProGuard {}, fBlindsT0 {}, fBlindsT1T2T3T4 {}, fX10 {}, fARC {}, fAC {}, fHomeEasyEU {}, fMeiantech {}, fOregonScientific {}, fATI {}, fVisonic {}, fKeeLoq {}, fHomeConfort {}, fRFU2 {}, fRFU3 {}, fRFU4 {}, fRFU5 {}, fRFU6 {}, fRFU7 {}, dummy7 {}, dummy8 {}, dummy9 {}".format(eSubtype, cSeqnbr, eCmnd, dummy1, dummy2, fAEBlyss, fRubicson, fFineOffsetViking, fLighting4, fRSL, fByronSX, fRFU, fUndecoded, fMertik, fADLightwaveRF, fHidekiUPM, fLaCrosse, fFS20, fProGuard, fBlindsT0, fBlindsT1T2T3T4, fX10, fARC, fAC, fHomeEasyEU, fMeiantech, fOregonScientific, fATI, fVisonic, fKeeLoq, fHomeConfort, fRFU2, fRFU3, fRFU4, fRFU5, fRFU6, fRFU7, dummy7, dummy8, dummy9))
            pass

    r = RFXTest()

    d = r.generate(
        type='InterfaceControl',
        eSubtype='Interface Control',
        cSeqnbr=0,
        eCmnd="reset",
        dummy1=33,
        dummy2=44,
        fAEBlyss=0,
        fRubicson=0,
        fFineOffsetViking=0,
        fLighting4=0,
        fRSL=0,
        fByronSX=0,
        fRFU=0,
        fUndecoded=0,
        fMertik=1,
        fADLightwaveRF=0,
        fHidekiUPM=0,
        fLaCrosse=0,
        fFS20=0,
        fProGuard=0,
        fBlindsT0=0,
        fBlindsT1T2T3T4=0,
        fX10=0,
        fARC=0,
        fAC=0,
        fHomeEasyEU=0,
        fMeiantech=0,
        fOregonScientific=0,
        fATI=0,
        fVisonic=0,
        fKeeLoq=0,
        fHomeConfort=0,
        fRFU2=0,
        fRFU3=0,
        fRFU4=0,
        fRFU5=0,
        fRFU6=0,
        fRFU7=1,
        dummy7=7,
        dummy8=8,
        dummy9=9,
    )
    r.dataReceived(d)
