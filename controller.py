"""
POX Controller for SDN Project
Features:
- Learning Switch (L2 Forwarding - similar to built-in l2_learning)
- Firewall (Blocks communication between h1 and h4)
- Traffic Monitoring (Periodically collects and logs flow statistics)
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.util import dpid_to_str
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.recoco import Timer

log = core.getLogger()

class FirewallLearningSwitch(object):
    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)
        
        # MAC to Port mapping table
        self.mac_to_port = {}
        
        # Start a periodic timer to request flow statistics (every 10 seconds)
        Timer(10, self._request_stats, recurring=True)

    def _request_stats(self):
        """Sends a request to the switch for flow statistics"""
        log.debug("Requesting flow stats for switch %s", dpid_to_str(self.connection.dpid))
        self.connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))

    def _handle_FlowStatsReceived(self, event):
        """Called when flow statistics are received from the switch"""
        stats = event.stats
        
        print("\n\n" + "=" * 60)
        print("          TRAFFIC MONITORING STATS (Flow Table)          ")
        print("=" * 60)
        print("{:<10} | {:<10} | {:<12} | {}".format("PRIORITY", "PACKETS", "BYTES", "MATCH REQ"))
        print("-" * 60)
        
        # Sort by priority
        sorted_stats = sorted(stats, key=lambda f: f.priority, reverse=True)
        
        for f in sorted_stats:
            # We don't print the totally empty table miss or extremely low priority ones here, 
            # just active rules for clarity. However, in OpenFlow 1.0, active flows are generally non-zero priority.
            if f.priority > 0:
                print("{:<10} | {:<10} | {:<12} | {}".format(f.priority, f.packet_count, f.byte_count, f.match))
        print("=" * 60 + "\n")

    def _handle_PacketIn(self, event):
        """Handles packet incoming from the switch"""
        packet = event.parsed
        
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packet_in = event.ofp

        # 1. Firewall Logic (IP Layer checking)
        if packet.type == packet.IP_TYPE:
            ip_packet = packet.next
            if isinstance(ip_packet, ipv4):
                ip_src = ip_packet.srcip
                ip_dst = ip_packet.dstip
                
                # Check if traffic is between 10.0.0.1 (H1) and 10.0.0.4 (H4)
                if (ip_src == IPAddr("10.0.0.1") and ip_dst == IPAddr("10.0.0.4")) or \
                   (ip_src == IPAddr("10.0.0.4") and ip_dst == IPAddr("10.0.0.1")):
                    
                    log.warning("[FIREWALL] Dropping packet from %s to %s", ip_src, ip_dst)
                    
                    # Install drop flow
                    msg = of.ofp_flow_mod()
                    msg.match = of.ofp_match.from_packet(packet)
                    msg.idle_timeout = 60
                    msg.priority = 100
                    # Empty actions means DROP
                    self.connection.send(msg)
                    return

        # 2. Learning Switch Logic
        self.mac_to_port[packet.src] = event.port

        if packet.dst in self.mac_to_port:
            out_port = self.mac_to_port[packet.dst]

            if out_port == event.port:
                # Same port, don't formulate loop
                log.warning("Port matched incoming port. Discarding loop.")
                return

            # Install a flow rule for forwarding to learned port
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet)
            msg.idle_timeout = 15
            msg.hard_timeout = 30
            msg.priority = 10
            msg.actions.append(of.ofp_action_output(port=out_port))
            
            # Piggyback the packet so we don't have to send a packet_out separately
            msg.data = event.ofp
            self.connection.send(msg)

        else:
            # Destination MAC is unknown, FLOOD the packet
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            msg.data = event.ofp
            msg.in_port = event.port
            self.connection.send(msg)

def launch():
    """
    Starts the component
    """
    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        FirewallLearningSwitch(event.connection)

    # Listen to ConnectionUp events
    core.openflow.addListenerByName("ConnectionUp", start_switch)
    log.info("POX Controller initialized and waiting for connections...")
