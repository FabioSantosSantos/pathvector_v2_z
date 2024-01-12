/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * Copyright (c) 2011-2015  Regents of the University of California.
 *
 * This file is part of ndnSIM. See AUTHORS for complete list of ndnSIM authors and
 * contributors.
 *
 * ndnSIM is free software: you can redistribute it and/or modify it under the terms
 * of the GNU General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 *
 * ndnSIM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
 * without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
 * PURPOSE.  See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * ndnSIM, e.g., in COPYING.md file.  If not, see <http://www.gnu.org/licenses/>.
 **/

// ndn-grid.cpp
//
#include "ndvr-app.hpp"
#include "ndvr-security-helper.hpp"

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/point-to-point-layout-module.h"
#include "ns3/ndnSIM-module.h"

namespace ns3 {

/**
 * This scenario simulates a grid topology (using PointToPointGrid module)
 *
 *     NS_LOG=ndn.Consumer:ndn.Producer ./waf --run=ndn-grid
 */
NS_OBJECT_ENSURE_REGISTERED(NdvrApp);

int
main(int argc, char* argv[])
{
  int numNodes = 3;
  // Setting default parameters for PointToPoint links and channels
  Config::SetDefault("ns3::PointToPointNetDevice::DataRate", StringValue("1Mbps"));
  Config::SetDefault("ns3::PointToPointChannel::Delay", StringValue("0ms"));

  // Read optional command-line parameters (e.g., enable visualizer with ./waf --run=<> --visualize
  CommandLine cmd;
  cmd.AddValue("numNodes", "numNodes", numNodes);
  cmd.Parse(argc, argv);

  // Creating NxN topology
  PointToPointHelper p2p;
  PointToPointGridHelper grid(numNodes, numNodes, p2p);
  grid.BoundingBox(100, 100, 400, 400);

  // Install NDN stack on all nodes
  ndn::StackHelper ndnHelper;
  ndnHelper.InstallAll();

  // Set BestRoute strategy
  ndn::StrategyChoiceHelper::InstallAll("/", "/localhost/nfd/strategy/multicast");

  // Security - create root cert (to be used as trusted anchor later)
  std::string network = "/ndn";
  ::ndn::ndvr::setupRootCert(ndn::Name(network), "config/trust.cert");

  // data prefix
  std::string prefix = "/ndn/dataSync";

  // 5. Install NDN Apps (Ndvr)
  uint64_t idx = 0;
  for (int i=0; i < numNodes; i++) {
    for (int j=0; j < numNodes; j++) {
      Ptr<Node> node = grid.GetNode(i, j);
      std::string routerName = "/\%C1.Router/Router"+std::to_string(idx);

      ndn::AppHelper appHelper("NdvrApp");
      appHelper.SetAttribute("Network", StringValue("/ndn"));
      appHelper.SetAttribute("RouterName", StringValue(routerName));
      appHelper.Install(node);

      auto app = DynamicCast<NdvrApp>(node->GetApplication(0));
      app->AddSigningInfo(::ndn::ndvr::setupSigningInfo(ndn::Name(network + routerName), ndn::Name(network)));
      if (i == numNodes-1 && j == numNodes-1)
        app->AddNamePrefix(prefix);

      idx += 1;
    }
  }

  // Getting containers for the consumer/producer
  Ptr<Node> producer = grid.GetNode(numNodes-1, numNodes-1);
  Ptr<Node> consumer = grid.GetNode(0, 0);

  // Install Data applications
  ndn::AppHelper consumerHelper("ns3::ndn::ConsumerCbr");
  consumerHelper.SetPrefix(prefix);
  consumerHelper.SetAttribute("Frequency", StringValue("10")); // 10 interests a second
  consumerHelper.Install(consumer);

  ndn::AppHelper producerHelper("ns3::ndn::Producer");
  producerHelper.SetPrefix(prefix);
  producerHelper.SetAttribute("PayloadSize", StringValue("1024"));
  producerHelper.Install(producer);

  Simulator::Stop(Seconds(100.0));

  Simulator::Run();
  Simulator::Destroy();

  return 0;
}

} // namespace ns3

int
main(int argc, char* argv[])
{
  return ns3::main(argc, argv);
}