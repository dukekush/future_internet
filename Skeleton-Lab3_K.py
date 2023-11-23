from pox.core import core
from collections import defaultdict

import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery
import pox.openflow.spanning_tree

from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.util import dpidToStr

from pox.lib.addresses import IPAddr, EthAddr
from collections import namedtuple
import os


log = core.getLogger()

class CustomSlice (EventMixin):
	def __init__(self):
		self.listenTo(core.openflow)
		core.openflow_discovery.addListeners(self)

		# Adjacency map.  [sw1][sw2] -> port from sw1 to sw2
		self.adjacency = defaultdict(lambda:defaultdict(lambda:None))

		'''
		We suggest an structure that relates origin-destination MAC address and port:
		(dpid, origin MAC, destination MAC, port : following dpid)
		The structure of self.portmap is a four-tuple key and a string value.
		The type is:
		(dpid string, src MAC addr, dst MAC addr, port (int)) -> dpid of next switch
		'''

		self.portmap = {
						# Host 1 UDP
                        ('00-00-00-00-00-01', EthAddr('00:00:00:00:00:01'),
                         EthAddr('00:00:00:00:00:05'), 200): '00-00-00-00-00-04',
						 ('00-00-00-00-00-04', EthAddr('00:00:00:00:00:01'),
                         EthAddr('00:00:00:00:00:05'), 200): '00-00-00-00-00-07',
						# Host 2 UDP
                        ('00-00-00-00-00-02', EthAddr('00:00:00:00:00:02'),
                         EthAddr('00:00:00:00:00:05'), 200): '00-00-00-00-00-01',
						('00-00-00-00-00-01', EthAddr('00:00:00:00:00:02'),
                         EthAddr('00:00:00:00:00:05'), 200): '00-00-00-00-00-04',
						('00-00-00-00-00-04', EthAddr('00:00:00:00:00:02'),
                         EthAddr('00:00:00:00:00:05'), 200): '00-00-00-00-00-07',
						# Host 2 TCP
						('00-00-00-00-00-02', EthAddr('00:00:00:00:00:02'),
                         EthAddr('00:00:00:00:00:06'), 80): '00-00-00-00-00-05',
						('00-00-00-00-00-05', EthAddr('00:00:00:00:00:02'),
                         EthAddr('00:00:00:00:00:06'), 80): '00-00-00-00-00-07',
						# Host 3 TCP
						('00-00-00-00-00-03', EthAddr('00:00:00:00:00:03'),
                         EthAddr('00:00:00:00:00:06'), 80): '00-00-00-00-00-06',
						('00-00-00-00-00-06', EthAddr('00:00:00:00:00:03'),
                         EthAddr('00:00:00:00:00:06'), 80): '00-00-00-00-00-07',
						# Host 4 TCP
						('00-00-00-00-00-03', EthAddr('00:00:00:00:00:04'),
                         EthAddr('00:00:00:00:00:06'), 80): '00-00-00-00-00-06',
						('00-00-00-00-00-06', EthAddr('00:00:00:00:00:04'),
                         EthAddr('00:00:00:00:00:06'), 80): '00-00-00-00-00-07',
						# Server 5
						## Host 1
						('00-00-00-00-00-07', EthAddr('00:00:00:00:00:05'),
                         EthAddr('00:00:00:00:00:01'), 200): '00-00-00-00-00-04',
						 ('00-00-00-00-00-04', EthAddr('00:00:00:00:00:05'),
                         EthAddr('00:00:00:00:00:01'), 200): '00-00-00-00-00-01',
						 ## Host 2
						 ('00-00-00-00-00-07', EthAddr('00:00:00:00:00:05'),
                         EthAddr('00:00:00:00:00:02'), 200): '00-00-00-00-00-04',
						 ('00-00-00-00-00-04', EthAddr('00:00:00:00:00:05'),
                         EthAddr('00:00:00:00:00:02'), 200): '00-00-00-00-00-01',
						 ('00-00-00-00-00-01', EthAddr('00:00:00:00:00:05'),
                         EthAddr('00:00:00:00:00:02'), 200): '00-00-00-00-00-02',
						 # Server 5
						## Host 2
						('00-00-00-00-00-07', EthAddr('00:00:00:00:00:06'),
                         EthAddr('00:00:00:00:00:02'), 80): '00-00-00-00-00-05',
						('00-00-00-00-00-05', EthAddr('00:00:00:00:00:06'),
                         EthAddr('00:00:00:00:00:02'), 80): '00-00-00-00-00-02',
						 ## Host 3
						('00-00-00-00-00-07', EthAddr('00:00:00:00:00:06'),
                         EthAddr('00:00:00:00:00:03'), 80): '00-00-00-00-00-06',
						('00-00-00-00-00-06', EthAddr('00:00:00:00:00:06'),
                         EthAddr('00:00:00:00:00:03'), 80): '00-00-00-00-00-03',
						 ## Host 4
						('00-00-00-00-00-07', EthAddr('00:00:00:00:00:06'),
                         EthAddr('00:00:00:00:00:04'), 80): '00-00-00-00-00-06',
						('00-00-00-00-00-06', EthAddr('00:00:00:00:00:06'),
                         EthAddr('00:00:00:00:00:04'), 80): '00-00-00-00-00-03',
		}
		self.host_port_map = {
            '00:00:00:00:00:01': 1,
            '00:00:00:00:00:02': 2,
            '00:00:00:00:00:03': 2,
            '00:00:00:00:00:04': 3,
            '00:00:00:00:00:05': 4,
            '00:00:00:00:00:06': 5,
        }
	def _handle_ConnectionUp(self, event):
		dpid = dpidToStr(event.dpid)
		log.debug("Switch %s has connected.", dpid)

	def _handle_LinkEvent (self, event):
		l = event.link
		sw1 = dpid_to_str(l.dpid1)
		sw2 = dpid_to_str(l.dpid2)
		log.debug ("link %s[%d] <-> %s[%d]",
			sw1, l.port1,
			sw2, l.port2)
		self.adjacency[sw1][sw2] = l.port1
		self.adjacency[sw2][sw1] = l.port2

		

	def _handle_PacketIn (self, event):
		"""
		Handle packet in messages from the switch to implement above algorithm.
		"""
		packet = event.parsed
		tcpp = event.parsed.find('tcp')
		udpp = event.parsed.find('udp')
		'''tcpp=80'''

		# flood, but don't install the rule
		def flood (message = None):
			""" Floods the packet """
			msg = of.ofp_packet_out()
			msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
			msg.data = event.ofp
			msg.in_port = event.port
			event.connection.send(msg)
		
		def install_fwdrule(event,packet,outport):
			msg = of.ofp_flow_mod()
			msg.idle_timeout = 10
			msg.hard_timeout = 30
			msg.match = of.ofp_match.from_packet(packet, event.port)
			msg.actions.append(of.ofp_action_output(port = outport))
			msg.data = event.ofp
			msg.in_port = event.port
			event.connection.send(msg)

		
		def forward (message = None):
			this_dpid = dpid_to_str(event.dpid)
			if packet.dst.is_multicast:
				flood()
				return
			else:
				log.debug("Got unicast packet for %s at %s (input port %d):",packet.dst, dpid_to_str(event.dpid), event.port)
				
				try:
					# Check for the the ARP
					if packet.type == 2054:
						log.debug(f"Got ARP on the switch: {this_dpid}")
						flood()
					# frame type is IPv4
					elif packet.type == 2048:
						if tcpp is not None:
							log.debug(f'The TCP found on {this_dpid} switch.')
							# add the rule based on the source port
							if (this_dpid, packet.src, packet.dst, tcpp.srcport) in self.portmap.keys():
								log.debug(f'The TCP source.')
								src_map = self.portmap[(this_dpid, packet.src, packet.dst, tcpp.srcport)]
								outport = self.adjacency[this_dpid][src_map]
							# add the rule based on the destination port
							elif (this_dpid, packet.src, packet.dst, tcpp.dstport) in self.portmap.keys():
								log.debug(f'The TCP dst.')
								dst_map = self.portmap[(this_dpid, packet.src, packet.dst, tcpp.dstport)]
								outport = self.adjacency[this_dpid][dst_map]
							# add rules between host and switch
							else:
								log.debug(f'Host Switch.')
								outport = self.host_port_map[str(packet.dst)]
							install_fwdrule(event, packet, outport)

						elif udpp is not None:
							log.debug(f'The UDP found on {this_dpid} switch.')
							if (this_dpid, packet.src, packet.dst, udpp.srcport) in self.portmap.keys():
								log.debug(f'The UDP source.')
								src_map = self.portmap[(this_dpid, packet.src, packet.dst, udpp.srcport)]
								outport = self.adjacency[this_dpid][src_map]
							elif (this_dpid, packet.src, packet.dst, udpp.dstport) in self.portmap.keys():
								log.debug(f'The UDP dst.')
								dst_map = self.portmap[(this_dpid, packet.src, packet.dst, udpp.dstport)]
								outport = self.adjacency[this_dpid][dst_map]
							else:
								outport = self.host_port_map[str(packet.dst)]
							install_fwdrule(event, packet,outport)
						
						elif packet.payload.protocol == 1:
							log.debug("Got ICMP on the switch: {this_dpid}")
							flood()

				except AttributeError:
					log.debug("packet type has no transport ports, flooding")

					# flood and install the flow table entry for the flood
					install_fwdrule(event, packet, of.OFPP_FLOOD)
		forward()

def launch():
	# Ejecute spanning tree para evitar problemas con topologías con bucles
	pox.openflow.discovery.launch()
	pox.openflow.spanning_tree.launch()

	core.registerNew(CustomSlice)

