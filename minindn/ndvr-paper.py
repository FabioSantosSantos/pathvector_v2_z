# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2015-2019, The University of Memphis,
#                          Arizona Board of Regents,
#                          Regents of the University of California.
#
# This file is part of Mini-NDN.
# See AUTHORS.md for a complete list of Mini-NDN authors and contributors.
#
# Mini-NDN is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mini-NDN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mini-NDN, e.g., in COPYING.md file.
# If not, see <http://www.gnu.org/licenses/>.

import time

from mininet.log import lg, setLogLevel, info
import logging
from mininet.clean import sh
from minindn.minindn import Minindn
from minindn.util import MiniNDNCLI
from minindn.apps.app_manager import AppManager
from minindn.apps.nfd import Nfd
from apps.ndvr import Ndvr
from minindn.helpers.experiment import Experiment
from minindn.helpers.nfdc import Nfdc

import argparse

def mysleep(duration):
    info('Sleep for {} seconds\n'.format(duration))
    time.sleep(duration)

def getParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=None,
                        help='NDVR Hello Interval')
    parser.add_argument('--no-cli', action='store_false', dest='isCliEnabled',
                        help='Run experiments and exit without showing the command line interface')
    parser.add_argument('--nPings', type=int, default=300,
                        help='Number of pings to perform between each node in the experiment')
    parser.add_argument('--ctime', type=int, default=60,
                        help='Specify convergence time for the topology (Default: 60 seconds)')
    parser.add_argument('--pct-traffic', dest='pctTraffic', type=float, default=1.0,
                        help='Specify the percentage of nodes each node should ping')
    parser.add_argument('--vbr', action='store_true', dest='enableVBR',
                        help='Run ping with Variable Bit Rate traffic model')
    parser.add_argument('--onoff', action='store_true', dest='enableOnOff',
                        help='Enable On/Off failure model for the most connected node')
    return parser

def mcnFailure(ndn, nfds, ndvrs, args):
    sh('dstat --epoch --cpu --mem > {}/dstat 2>&1 & echo $! > {}/dstat.pid'.format(args.workDir, args.workDir))
    sh('/usr/local/bin/get-cpu-usage.sh ndvrd > {}/get-cpu-usage-ndvrd 2>&1 & echo $! > {}/get-cpu-usage-ndvrd.pid'.format(args.workDir, args.workDir))
    sh('/usr/local/bin/get-cpu-usage.sh ndnping > {}/get-cpu-usage-ndnping 2>&1 & echo $! > {}/get-cpu-usage-ndnping.pid'.format(args.workDir, args.workDir))
    sh('/usr/local/bin/get-cpu-usage.sh ndnpingserver > {}/get-cpu-usage-ndnpingserver 2>&1 & echo $! > {}/get-cpu-usage-ndnpingserver.pid'.format(args.workDir, args.workDir))
    sh('top -b -d 1 > {}/top 2>&1 & echo $! > {}/top.pid'.format(args.workDir, args.workDir))
    mysleep(args.ctime)

    mysleep(120)

    if args.nPings != 0:
        if args.enableVBR:
            Experiment.setupPing(ndn.net.hosts, Nfdc.STRATEGY_BEST_ROUTE, options='--udist-size 400,1200')
            pingedDict = Experiment.startPctPings(ndn.net, args.nPings, args.pctTraffic, options='--poisson-interval 1000')
        else:
            Experiment.setupPing(ndn.net.hosts, Nfdc.STRATEGY_BEST_ROUTE, options='--size 800')
            pingedDict = Experiment.startPctPings(ndn.net, args.nPings, args.pctTraffic)

    mcn = max(ndn.net.hosts, key=lambda host: len(host.intfNames()))
    if args.enableOnOff:
        nPings = args.nPings
        while nPings >= 60:
            mysleep(30)
            info('Bringing down node {}\n'.format(mcn.name))
            ndvrs[mcn.name].stop()
            nfds[mcn.name].stop()
            mysleep(30)
            info('Bringing up node {}\n'.format(mcn.name))
            nfds[mcn.name].start()
            ndvrs[mcn.name].start()
            nPings = nPings - 60

    else:
        mysleep(60)

        info('Bringing down node {}\n'.format(mcn.name))
        for i in mcn.intfs:
            mcn.intfs[i].link.intf1.config(loss=100.0)
            mcn.intfs[i].link.intf2.config(loss=100.0)
            #mcn.cmd("ip link set down %s" % mcn.intfs[i].name)
        #ndvrs[mcn.name].stop()
        #nfds[mcn.name].stop()

        mysleep(60)

        info('Bringing up node {}\n'.format(mcn.name))
        for i in mcn.intfs:
            mcn.intfs[i].link.intf1.config(loss=0.000001)
            mcn.intfs[i].link.intf2.config(loss=0.000001)
            #mcn.cmd("ip link set up %s" % mcn.intfs[i].name)
        #nfds[mcn.name].start()
        #ndvrs[mcn.name].start()

    mysleep(60)
    sh('pkill -F {}/dstat.pid'.format(args.workDir))
    sh('pkill -F {}/get-cpu-usage-ndvrd.pid'.format(args.workDir))
    sh('pkill -F {}/get-cpu-usage-ndnping.pid'.format(args.workDir))
    sh('pkill -F {}/get-cpu-usage-ndnpingserver.pid'.format(args.workDir))
    sh('pkill -F {}/top.pid'.format(args.workDir))

if __name__ == '__main__':
    lg.ch.formatter = logging.Formatter('%(asctime)s - %(message)s')
    setLogLevel('info')
    ndn = Minindn(parser=getParser())
    args = ndn.args

    info('Starting Minindn\n')
    ndn.start()

    info('Starting nfd\n')
    nfds = AppManager(ndn, ndn.net.hosts, Nfd, logLevel='DEBUG')
    info('Starting ndvr\n')
    ndvrs = AppManager(ndn, ndn.net.hosts, Ndvr, logLevel='ndvr.*=DEBUG', network="/n", router_name="C1.R", interval=args.interval)

    info('Starting mcnFailure()\n')
    mcnFailure(ndn, nfds, ndvrs, args)

    if args.isCliEnabled:
        MiniNDNCLI(ndn.net)

    ndn.stop()
