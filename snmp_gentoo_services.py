#!/bin/env python3
# Copyright © 2012 Binet Réseau
# See the LICENCE file for more informations
"""Check Gentoo services with rc-status command

This script populates .1.3.6.1.4.1.34741.3 subtree of an SNMP server.
"""

import re
import subprocess
from optparse import OptionParser

# BR OID for services
OID_PREFIX = '.1.3.6.1.4.1.34741.3'


def rc_status(params):
    """Run rc-status with parameters and parse the output

    params -- List of string parameters

    Yield (service, status) tuples
    """
    if type(params) is str:
        params = [params]
    re_lvl = re.compile(r'^Runlevel: [a-z]+\s*$')
    re_srv = re.compile(r'^\s+(?P<srv>[-._a-zA-Z0-9]+)\s*'
                        r'\[\s*(?P<stat>[a-z]+)\s*\]\s*$')
    with subprocess.Popen(['/bin/rc-status', '--nocolor'] + params,
                          stdout=subprocess.PIPE) as proc:
        for line in proc.stdout:
            line = line.decode('ascii').rstrip()
            matches = re_srv.match(line)
            if matches:
                yield (matches.group('srv'), matches.group('stat'))
            elif line and not re_lvl.match(line):
                raise Exception("Unable to decode line '%s'" % line)
        proc.wait()


def stopped_services():
    """Get all non-started services, in a "srv:stopped" or "srv:crashed" syntax
    """
    for srv, status in rc_status(['sysinit', 'boot', 'default']):
        if status != 'started':
            yield srv + ':' + status


def started_services():
    """Get all started services """
    for srv, status in rc_status('--servicelist'):
        if status == 'started':
            yield srv


def manual_services():
    """Get all started services which are "unused", and not "needed" """
    needed_services = frozenset(['sysfs', 'udev-mount'])
    for srv, status in rc_status('--unused'):
        if status == 'started' and not srv in needed_services:
            yield srv


def stopped_vital_services():
    """Get all vital services which are not started"""
    vital_services = frozenset(['iptables', 'postfix', 'ntpd', 'sshd',
                                'syslog-ng', 'vixie-cron'])
    started = set(list(started_services()))
    return vital_services - started


def get_services_status():
    """Return one line describing the overall status of the services
    and the number of problems
    """
    stopped = list(stopped_services())
    vital = list(stopped_vital_services())
    manual = list(manual_services())
    stopped.sort()
    vital.sort()
    manual.sort()
    nbtotal = len(stopped) + len(vital) + len(manual)

    if nbtotal == 0:
        return ("OK", 0)

    status = []
    if len(stopped):
        status.append("%d stopped (%s)" %
                      (len(stopped), ', '.join(stopped)))
    if len(vital):
        status.append("%d vital stopped (%s)" %
                      (len(vital), ', '.join(vital)))
    if len(manual):
        status.append("%d manually started (%s)" %
                      (len(manual), ', '.join(manual)))
    return (', '.join(status), nbtotal)


def parse_oid(oid):
    """Parse an OID and return (oid1, oid2) tuple"""
    # Check OID
    if not oid.startswith(OID_PREFIX):
        raise KeyError("Invalid OID")
    suffix = oid[len(OID_PREFIX):]

    # Parse suffix in two numbers
    match = re.search(r'^(\.(?P<a>[0-9]+)(\.(?P<b>[0-9]+))?)?$', suffix)
    if match is None:
        raise KeyError("Unknown OID")
    oid1, oid2 = match.group('a', 'b')
    oid1 = 0 if oid1 is None else int(oid1)
    oid2 = 0 if oid2 is None else int(oid2)
    return (oid1, oid2)


def build_oid(oid1=None, oid2=None):
    """Build an OID string from (oid1, oid2)"""
    oid1 = ('.' + str(oid1)) if oid1 else ''
    oid2 = ('.' + str(oid2)) if oid2 else ''
    return OID_PREFIX + oid1 + oid2


def next_oid(oid):
    """Find the next oid for the GETNEXT logic"""
    oid1, oid2 = parse_oid(oid)
    if oid1 == 0:
        oid1 = 1
    elif oid2 == 0:
        oid2 = 1
    elif oid1 < 5 and oid2 == 1:
        oid1 = oid1 + 1
        oid2 = 0
    else:
        raise KeyError("No next OID")
    return build_oid(oid1, oid2)


def get_text_num_by_oid(oid1):
    """Get (text, num) tuple corresponding to the given OID suffix"""
    # .1 is for general status
    if oid1 == 1:
        text, num = get_services_status()
        return (text, num)
    # Other branches are lists
    elements = None
    if oid1 == 2:
        elements = started_services()
    elif oid1 == 3:
        elements = stopped_services()
    elif oid1 == 4:
        elements = stopped_vital_services()
    elif oid1 == 5:
        elements = manual_services()
    else:
        raise KeyError("Unknown OID")

    # Transform elements to (text, num)
    if not type(elements) is list:
        elements = list(elements)
    elements.sort()
    return (', '.join(elements), len(elements))


def process_oid(oid):
    """Process an OID and print the associated result"""
    oid1, oid2 = parse_oid(oid)
    # .a is a length or a number, .a.1 is the list in a string
    (text, num) = get_text_num_by_oid(oid1)

    if oid2 == 0:
        print(oid)
        print('INTEGER')
        print(num)
    elif oid2 == 1:
        print(oid)
        print('STRING')
        print(text)

    return None


def main():
    """Main"""
    parser = OptionParser()
    parser.add_option('-g', None, dest='getoid',
                      help="GET OID request", metavar="OID")
    parser.add_option('-n', None, dest='nextoid',
                      help="GETNEXT OID request", metavar="OID")
    (options, args) = parser.parse_args()
    if len(args) > 0:
        parser.error("too many arguments")
    try:
        if options.getoid:
            process_oid(options.getoid)
        elif options.nextoid:
            process_oid(next_oid(options.nextoid))
    except KeyError:
        pass

if __name__ == '__main__':
    main()
