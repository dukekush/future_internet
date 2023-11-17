from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr
from pox.lib.revent import EventMixin
import pandas as pd

log = core.getLogger()

# Read csv file
file_path = 'pox/misc/firewall-policies.csv'
firewall_policies = pd.read_csv(file_path)

class Firewall(EventMixin):
    def __init__ (self):
        self.listenTo(core.openflow)

        log.debug("Activating Firewall")
    
    def _handle_ConnectionUp (self, event):  
        for _, (row) in firewall_policies.iterrows():

            # Create match
            match = of.ofp_match()
            # Source Adress
            match.dl_src = EthAddr(row['mac_0'])
            # Destination Adress
            match.dl_dst = EthAddr(row['mac_1'])
            # Flow modification
            flow_mod = of.ofp_flow_mod()
            # Connect with given match
            flow_mod.match = match
            # Inform the switch
            event.connection.send(flow_mod)
        
        # log the changes
        log.debug("Installed rules in %s", dpidToStr(event.dpid))

def launch ():

    core.registerNew(Firewall)