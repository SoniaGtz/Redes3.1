#
# USO: python3 Analyze.py <filename>.json IP|SERVICE <ip|service>
#

from datetime import datetime
import ipaddress
import json
import os.path
import sys
import socket
from collections import namedtuple

Pair = namedtuple('Pair', 'src dest')

def getIPs(flow):
    use_ipv4 = False  # optimistic default case of IPv6

    if 'IP_PROTOCOL_VERSION' in flow and flow['IP_PROTOCOL_VERSION'] == 4:
        use_ipv4 = True
    elif 'IPV4_SRC_ADDR' in flow or 'IPV4_DST_ADDR' in flow:
        use_ipv4 = True

    if use_ipv4:
        return Pair(
            ipaddress.ip_address(flow['IPV4_SRC_ADDR']),
            ipaddress.ip_address(flow['IPV4_DST_ADDR']))

    # else: return IPv6 pair
    return Pair(
        ipaddress.ip_address(flow['IPV6_SRC_ADDR']),
        ipaddress.ip_address(flow['IPV6_DST_ADDR']))


def humanSize(size):
    if size < 1024:
        return "%dB" % size
    elif size / 1024. < 1024:
        return "%.2fK" % (size / 1024.)
    elif size / 1024. ** 2 < 1024:
        return "%.2fM" % (size / 1024. ** 2)
    else:
        return "%.2fG" % (size / 1024. ** 3)

class Connection:
    """Connection model for two flows.
    The direction of the data flow can be seen by looking at the size.
    'src' describes the peer which sends more data towards the other. This
    does NOT have to mean, that 'src' was the initiator of the connection.
    """
    def __init__(self, flow1, flow2):
        if flow1['IN_BYTES'] >= flow2['IN_BYTES']:
            src = flow1
            dest = flow2
        else:
            src = flow2
            dest = flow1

        ips = getIPs(src)
        self.src = ips.src
        self.dest = ips.dest
        self.src_port = src['L4_SRC_PORT']
        self.dest_port = src['L4_DST_PORT']
        self.size = src['IN_BYTES']

        # Duration is given in milliseconds
        self.duration = src['LAST_SWITCHED'] - src['FIRST_SWITCHED']
        if self.duration < 0:
            # 32 bit int has its limits. Handling overflow here
            self.duration = (2**32 - src['FIRST_SWITCHED']) + src['LAST_SWITCHED']

    def __repr__(self):
        return "<Connection from {} to {}, size {}>".format(
            self.src, self.dest, self.human_size)

    @property
    def human_size(self):
        # Calculate a human readable size of the traffic
        if self.size < 1024:
            return "%dB" % self.size
        elif self.size / 1024. < 1024:
            return "%.2fK" % (self.size / 1024.)
        elif self.size / 1024.**2 < 1024:
            return "%.2fM" % (self.size / 1024.**2)
        else:
            return "%.2fG" % (self.size / 1024.**3)

    @property
    def human_duration(self):
        duration = self.duration // 1000  # uptime in milliseconds, floor it
        if duration < 60:
            # seconds
            return "%d sec" % duration
        if duration / 60 > 60:
            # hours
            return "%d:%02d.%02d hours" % (duration / 60**2, duration % 60**2 / 60, duration % 60)
        # minutes
        return "%02d:%02d min" % (duration / 60, duration % 60)

    @property
    def hostnames(self):
        # Resolve the IPs of this flows to their hostname
        src_hostname = socket.getfqdn(self.src.compressed)
        dest_hostname = socket.getfqdn(self.dest.compressed)

        return Pair(src_hostname, dest_hostname)

    @property
    def service(self):
        # Resolve ports to their services, if known
        service = "unknown"
        try:
            # Try service of sending peer first
            service = socket.getservbyport(self.src_port)
        except OSError:
            # Resolving the sport did not work, trying dport
            try:
                service = socket.getservbyport(self.dest_port)
            except OSError:
                pass
        return service


def cargar_json(filename):
    resultado = []
    if not os.path.exists(filename):
        exit("File {} does not exist!".format(filename))
    with open(filename, 'r') as fh:
        data = json.loads(fh.read())

    for export in sorted(data):
        timestamp = datetime.fromtimestamp(float(export)).strftime("%Y-%m-%d %H:%M:%S")

        flows = data[export]
        pending = None  # Two flows normally appear together for duplex connection
        for flow in flows:
            con = Connection(flow, flow)
            resultado.append([timestamp, con.service, con.size, str(con.src), str(con.dest)])

    os.remove(filename)
    with open(filename, 'w') as fh:
        json.dump({}, fh)
    return resultado

"""

# Handle CLI args and load the data dump
option = ""
parameter = ""
if len(sys.argv) < 2:
    exit("Use {} <filename>.json".format(sys.argv[0]))
elif len(sys.argv) == 3:
    exit("Use {} <filename>.json IP|SERVICE <ip|service>".format(sys.argv[0]))
elif len(sys.argv) == 4:
    option = sys.argv[2]
    parameter = sys.argv[3]
filename = sys.argv[1]

if not os.path.exists(filename):
    exit("File {} does not exist!".format(filename))
with open(filename, 'r') as fh:
    data = json.loads(fh.read())

if option != "IP" and option !="SERVICE" and option != "" and option != "BAND":
    exit("{} is not a valid option".format(option))


# Go through data and disect every flow saved inside the dump

band = 0
for export in sorted(data):
    timestamp = datetime.fromtimestamp(float(export)).strftime("%Y-%m-%d %H:%M.%S")

    flows = data[export]
    pending = None  # Two flows normally appear together for duplex connection
    for flow in flows:

        # if pending is not None:
            con = Connection(flow, flow)
            if (option == "") or (option == "IP" and str(con.src) == parameter) or (option == "SERVICE" and con.service.upper() == parameter):
                print("{timestamp}: {service:7} | {size:8} | {duration:9} | {src} to"\
                    " {dest}".format(
                    timestamp=timestamp, service=con.service.upper(), src=con.src, dest=con.dest,
                    size=con.human_size, duration=con.human_duration))

            elif option == "BAND" and (str(con.src) == parameter or str(con.dest) == parameter):
                band = band + con.size


        # flow = pending

if option == "BAND":
    bandwidth = float(band) / 600
    print(humanSize(bandwidth) + "/s ")

"""
