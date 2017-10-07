#!/usr/bin/env python3

from twisted.internet import protocol
from twisted.internet import task
from twisted.python import log

import struct
import os.path
import pkg_resources
import json
import logging
import binascii
import yamlstruct.yamlstruct


class RFXCOM(protocol.Protocol):
    def __init__(self):
        self.testTransportLoop = task.LoopingCall(self.testTransport)
        self.testTransportLoop.start(1.0)  # call every second
        self.yamlstructs = yamlstruct.yamlstruct.YamlStructs()
        for fileName in pkg_resources.resource_listdir("txrfxcom", 'protocol'):
            if fileName.startswith('.'): continue
            with pkg_resources.resource_stream("txrfxcom",
                                               "protocol/" + fileName) as f:
                self.yamlstructs.append(
                    yamlstruct.yamlstruct.YamlStruct(
                        os.path.basename(fileName)[:-4],
                        f
                    )
                )
        self.recvBuf = b''


    def testTransport(self):
        if (self.transport):
            self.testTransportLoop.stop()
            readyTransport = getattr(self, 'readyTransport', None)
            if (callable(readyTransport)):
                readyTransport()


    def generate(self, **args):
        typ = args["type"]
        del args["type"]
        b = self.yamlstructs.yamlstructs[typ].pack(args)
        return struct.pack('B', len(b)) + b


    def dataReceived(self, data):
        log.msg('dataReceived {}'.format(binascii.hexlify(data)), loglevel=logging.DEBUG)
        self.recvBuf += data
        pktlen = struct.unpack('B', self.recvBuf[:1])[0]
        if len(self.recvBuf) > pktlen:
            pkt = self.recvBuf[:pktlen + 1]
            self.recvBuf = self.recvBuf[pktlen + 1:]

            yamlstruct = self.yamlstructs.best_unpack(pkt[1:])
            if yamlstruct is None:
                log.msg("cannot find unpacker", loglevel=logging.DEBUG)
                return
            d = yamlstruct.unpack(pkt[1:])

            del d["type"]

            parser = getattr(self, "parse" + yamlstruct.name, None)
            if callable(parser):
                parser(**d)
            else:
                log.msg("parseDefault", loglevel=logging.DEBUG)
                self.parseDefault(yamlstruct.name, **d)


    def parseDefault(self, protocol, **args):
        log.msg("unhandled parse{0}({1})".format(protocol, ", ".join(
            args.keys())), loglevel=logging.DEBUG)
        log.msg(json.dumps(args, indent=4), loglevel=logging.DEBUG)



if __name__ == '__main__':
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
    print(d)
    r.dataReceived(d)
