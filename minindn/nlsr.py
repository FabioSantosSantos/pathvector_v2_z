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
import sys

from mininet.log import setLogLevel

from minindn.minindn import Minindn
from minindn.util import MiniNDNCLI
from minindn.apps.app_manager import AppManager
from minindn.apps.nfd import Nfd
from minindn.apps.nlsr import Nlsr

DEFAULT_TOPO = '/home/minindn/mini-ndn/examples/topo-two-nodes.conf'

if __name__ == '__main__':
    setLogLevel('info')
    topo_file = sys.argv[1] if len(sys.argv)>1 else DEFAULT_TOPO
    ndn = Minindn(topoFile=topo_file)
    args = ndn.args

    ndn.start()

    faceDict = {}
    for host in ndn.net.hosts:
        faceDict[host.name] = []
        for i in host.intfs:
            link = host.intfs[i].link
            neigh_intf = link.intf1
            if neigh_intf.node.name == host.name:
                neigh_intf = link.intf2
            faceDict[host.name].append([neigh_intf.node.name, host.intfs[i].name, 1])

    nfds = AppManager(ndn, ndn.net.hosts, Nfd, logLevel='DEBUG')
    #nlsrs = AppManager(ndn, ndn.net.hosts, Nlsr, faceDict=faceDict, faceType='ether', logLevel='ndn.*=DEBUG:nlsr.*=DEBUG') 
    nlsrs = AppManager(ndn, ndn.net.hosts, Nlsr, logLevel='ndn.*=DEBUG:nlsr.*=DEBUG') 

    MiniNDNCLI(ndn.net)

    ndn.stop()
