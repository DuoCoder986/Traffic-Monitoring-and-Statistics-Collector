"""
Mininet Custom Topology for SDN Project
Topology: 1 Switch, 4 Hosts
"""

from mininet.topo import Topo

class ProjectTopo(Topo):
    "Single switch connected to 4 hosts."

    def build(self):
        # Add a central switch
        switch = self.addSwitch('s1')

        # Add 4 hosts
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')

        # Add links between the switch and the hosts
        self.addLink(h1, switch)
        self.addLink(h2, switch)
        self.addLink(h3, switch)
        self.addLink(h4, switch)

topos = { 'custom': ( lambda: ProjectTopo() ) }
