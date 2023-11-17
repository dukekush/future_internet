'''
Assignment in class
'''

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import irange, dumpNodeConnections
from mininet.log import setLogLevel
# c 1
# a 1, 2
# e 1, 2, 3, 4
# h 1, .... 8

# c 1
# a 1, 2, 3
# e 1, 2, 3, 4, 5, 6, 7, 8, 9
# h 1, .... 27
#
class CustomTopo(Topo):
    "Simple Data Center Topology"

    "linkopts - (1:core, 2:aggregation, 3: edge) parameters"
    "fanout - number of child switch per parent switch"
    def __init__(self, linkopts1, linkopts2, linkopts3, fanout=2, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)
        self.linkopts = {1:linkopts1, 2:linkopts2, 3:linkopts3}

        self.k = fanout
        core_switch = self.addSwitch('c1')
        # aggregation layer
        for a in range(1, self.k ** 1 + 1):
            agg_switch = self.addSwitch('a%s' % a)
            self.addLink(core_switch, agg_switch, **linkopts1)
        for e in range(1, self.k ** 2 + 1):
            agg_num = (e + self.k - 1) // self.k
            edge_switch = self.addSwitch('e%s' % e)
            self.addLink(f'a{agg_num}', edge_switch, **linkopts2)
        for h in range(1, self.k**3 + 1):
             edge_num = (h + self.k - 1) // (self.k)
             host = self.addHost('h%s' % h)
             self.addLink(f'e{edge_num}', host, **linkopts3)
             

                    
def perfTest():
	"Create network and run simple performance test"
	linkopts1 = {'bw':10, 'delay':'50ms', 'loss':0.1, 'max_queue_size':1000, 'use_htb':True}
	linkopts2 = {'bw':100, 'delay':'10ms', 'loss':0.1, 'max_queue_size':1000, 'use_htb':True}
	linkopts3 = {'bw':1000, 'delay':'1ms', 'loss':0.1, 'max_queue_size':1000, 'use_htb':True}
	topo = CustomTopo(linkopts1,linkopts2,linkopts3,fanout=2)
	net = Mininet(topo=topo, link=TCLink)
    # net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
	net.start()
	print("Dumping host connections")
	dumpNodeConnections(net.hosts)
	print("Testing network connectivity")
	net.pingAll()
	print("Testing bandwidth between h1 and h2")
	h1, h2 = net.get('h1', 'h2')
	net.iperf((h1, h2))
	print("Testing bandwidth between h1 and h2")
	h1, h4 = net.get('h1', 'h4')
	net.iperf((h1, h4))	
	print("Testing bandwidth between h1 and h6")
	h1, h6 = net.get('h1', 'h6')
	net.iperf((h1, h6))
	net.stop()


if __name__ == '__main__':
   setLogLevel('info')
   perfTest()
