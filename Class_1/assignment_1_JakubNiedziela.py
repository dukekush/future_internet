from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.util import irange,dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import OVSSwitch, OVSBridge 
from mininet.nodelib import LinuxBridge
from mininet.link import TCLink


class CustomTopo(Topo):
	def __init__(self, n, **opts):
		Topo.__init__(self, **opts)
		self.n = n
		#Please insert your code here
		#We recommend to use the method self.addSwitch('s%s'%i, cls=OVSBridge, stp=True)
		#cls and stp parameters allows Mininet to use switchs that build a Spanning Tree
		switches = []
		for i in range(n):
			# Adds n hosts
			h = self.addHost(f'h{i + 1}')
			# Adds n switches 
			s = self.addSwitch(f's{i + 1}', cls=OVSBridge, stp=True)
			# Connects each host with corresponding switch
			self.addLink(s, h)
			# Connects switch with all other (list ensures there is n*(n-1)/2 connections between switches in total)
			for s2 in switches:
				self.addLink(s, s2)
			switches.append(s)


def runNet():
	topo=CustomTopo(4)
	net = Mininet(topo, host=CPULimitedHost, waitConnected=True, link=TCLink)
	net.start()
	dumpNodeConnections(net.hosts)
	net.pingAll()
	h1, h3 = net.get('h1', 'h3')
	net.iperf((h1, h3))
	net.stop()


if __name__ == '__main__':
	setLogLevel('info')
	runNet()
