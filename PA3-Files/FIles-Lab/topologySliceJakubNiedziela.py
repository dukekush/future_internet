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


class TopologySlice(EventMixin):

    def __init__(self):
        self.listenTo(core.openflow)
        log.debug("Enabling Slicing Module")


    def forward_rule(self, event, in_port, out_port):
        '''Add a rule to the switch'''

        log.debug("Adding forwarding rule on switch %s from port %s to port %s", dpidToStr(event.dpid), in_port, out_port)
        # Create match for given in port
        match = of.ofp_match(in_port=in_port)
        # Create action for given out port
        action = of.ofp_action_output(port=out_port)
        # Create message (flow rule modification)
        message = of.ofp_flow_mod(match=match, actions=[action])
        # Send message to switch -- add rule
        event.connection.send(message)
        
        
    """This event will be raised each time a switch will connect to the controller"""
    def _handle_ConnectionUp(self, event):
        
        # Use dpid to differentiate between switches (datapath-id)
        # Each switch has its own flow table. As we'll see in this 
        # example we need to write different rules in different tables.
        dpid = dpidToStr(event.dpid)
        log.debug("Switch %s has come up.", dpid)
        
        """ Add your logic here """
        
        # Switch 1 -- 4 ports
        if dpid == '00-00-00-00-00-01':
            pairs = [[1, 3], [2, 4]]
            # Add rule for both way of communication
            for pair in pairs:
                for start in pair:
                    for end in pair:
                        if start != end:  # Dissallow communication with itself
                            self.forward_rule(event, start, end)

        # Switch 2 -- 2 ports
        elif dpid == '00-00-00-00-00-02':
            pairs = [[1, 2]]
            # Add rule for both way of communication
            for pair in pairs:
                for start in pair:
                    for end in pair:
                        if start != end:  # Dissallow communication with itself
                            self.forward_rule(event, start, end)

        # Switch 3 -- 4 ports
        elif dpid == '00-00-00-00-00-03':
            pairs = [[1, 3], [2, 4]]
            # Add rule for both way of communication
            for pair in pairs:
                for start in pair:
                    for end in pair:
                        if start != end:  # Dissallow communication with itself
                            self.forward_rule(event, start, end)

        # Switch 4 -- 2 ports                    
        elif dpid == '00-00-00-00-00-04':
            pairs = [[1, 2]]
            # Add rule for both way of communication
            for pair in pairs:
                for start in pair:
                    for end in pair:
                        if start != end:  # Dissallow communication with itself
                            self.forward_rule(event, start, end)


def launch():
    # Run spanning tree so that we can deal with topologies with loops
    pox.openflow.discovery.launch()
    pox.openflow.spanning_tree.launch()

    '''
    Starting the Topology Slicing module
    '''
    core.registerNew(TopologySlice)