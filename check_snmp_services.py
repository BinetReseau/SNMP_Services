#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright © 2011-2012 Binet Réseau
"""Nagios plugin to check services through SNMP
"""

from optparse import OptionParser
from pysnmp.entity.rfc3413.oneliner import cmdgen
import sys


OID_SERVICES_STATUS_NUM = (1, 3, 6, 1, 4, 1, 34741, 3, 1)
OID_SERVICES_STATUS = (1, 3, 6, 1, 4, 1, 34741, 3, 1, 1)
OID_SERVICES_STARTED_NUM = (1, 3, 6, 1, 4, 1, 34741, 3, 2)
OID_SERVICES_STARTED = (1, 3, 6, 1, 4, 1, 34741, 3, 2, 1)
OID_SERVICES_STOPPED_NUM = (1, 3, 6, 1, 4, 1, 34741, 3, 3)
OID_SERVICES_STOPPED = (1, 3, 6, 1, 4, 1, 34741, 3, 3, 1)
OID_SERVICES_VITAL_NUM = (1, 3, 6, 1, 4, 1, 34741, 3, 4)
OID_SERVICES_VITAL = (1, 3, 6, 1, 4, 1, 34741, 3, 4, 1)
OID_SERVICES_MANUAL_NUM = (1, 3, 6, 1, 4, 1, 34741, 3, 5)
OID_SERVICES_MANUAL = (1, 3, 6, 1, 4, 1, 34741, 3, 5, 1)


def main():
    # Parse command line
    parser = OptionParser()
    parser.add_option('-H', '--hostname', dest='hostname',
        help="Host name, IP Address", metavar="HOSTNAME")
    parser.add_option('-p', '--port', dest='port', default=161,
        help="Port number (default: 161)", metavar="INTEGER")
    parser.add_option('-P', '--protocol', dest='protocol',
        help="SNMP protocol version", metavar="[1|2c|3]")
    parser.add_option('-L', '--seclevel', dest='seclevel',
        help="SNMPv3 security level",
        metavar="[noAuthNoPriv|authNoPriv|authPriv]")
    parser.add_option('-a', '--authproto', dest='authproto',
        help="SNMPv3 auth proto", metavar="[MD5|SHA]")
    parser.add_option('-x', '--privproto', dest='privproto', default="DES",
        help="SNMPv3 priv proto (default: DES)", metavar="[DES|3DES|AES]")
    parser.add_option('-C', '--community', dest='community', default="public",
        help="Optional community string (default: public)", metavar="STRING")
    parser.add_option('-U', '--secname', dest='secname',
        help="SNMPv3 username", metavar="USERNAME")
    parser.add_option('-A', '--authpassword', dest='authpassword',
        help="SNMPv3 authentication password", metavar="PASSWORD")
    parser.add_option('-X', '--privpasswd', dest='privpasswd',
        help="SNMPv3 privacy password", metavar="PASSWORD")
    (options, args) = parser.parse_args()

    # Convert command line to pysnmp language
    target = cmdgen.UdpTransportTarget((options.hostname, options.port))
    if options.protocol == '3':
        authproto = cmdgen.usmNoAuthProtocol
        if options.authproto == 'MD5':
            authproto = cmdgen.usmHMACMD5AuthProtocol
        elif options.authproto == 'SHA':
            authproto = cmdgen.usmHMACSHAAuthProtocol

        privproto = cmdgen.usmNoPrivProtocol
        if options.privproto == 'DES':
            privproto = cmdgen.usmDESPrivProtocol
        if options.privproto == '3DES':
            privproto = cmdgen.usm3DESEDEPrivProtocol
        if options.privproto == 'AES':
            privproto = cmdgen.usmAesCfb256Protocol

        auth_data = cmdgen.UsmUserData(options.secname,
                                       authKey=options.authpassword,
                                       privKey=options.privpasswd,
                                       authProtocol=authproto,
                                       privProtocol=privproto)
    else:
        auth_data = cmdgen.CommunityData(options.secname, options.community)

    # Invoke SNMP magic
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        auth_data, target,
        OID_SERVICES_STATUS,
        OID_SERVICES_STOPPED_NUM,
        OID_SERVICES_VITAL_NUM,
        OID_SERVICES_MANUAL_NUM)

    # Failure leads to an unknown status
    if errorIndication:
        print u"SNMP ERROR %s" % errorIndication
        sys.exit(3)
    elif errorStatus:
        print u"SNMP ERROR %s" % errorStatus
        sys.exit(3)

    # Decode result
    status = None
    stopped_num = None
    vital_num = None
    manual_num = None
    for name, val in varBinds:
        if name == OID_SERVICES_STATUS:
            status = val
            if not val:
                # There may be a no-such-instance error
                print u"SNMP value error: %s" % val.prettyPrint()
                sys.exit(3)
        elif name == OID_SERVICES_STOPPED_NUM:
            stopped_num = val
        elif name == OID_SERVICES_VITAL_NUM:
            vital_num = val
        elif name == OID_SERVICES_MANUAL_NUM:
            manual_num = val

    # Tests
    if stopped_num > 0 or vital_num > 0:
        print u"Services CRIT - %s" % status
        sys.exit(2)
    elif manual_num > 0:
        print u"Services WARN - %s" % status
        sys.exit(1)
    else:
        print u"Services OK - %s" % status
        sys.exit(0)

if __name__ == '__main__':
    main()
