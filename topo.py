"""
Topology:

    - 192.168.1.0/24 (r0-eth1, IP: 192.168.1.1)
    - 172.16.0.0/12 (r0-eth2, IP: 172.16.0.1)
    - 10.0.0.0/8 (r0-eth3, IP: 10.0.0.1)

Each subnet consists of a single host connected to
a single switch:

    r0-eth1 - s1-eth1 - h1-eth0 (IP: 192.168.1.100)
    r0-eth2 - s2-eth1 - h2-eth0 (IP: 172.16.0.100)
    r0-eth3 - s3-eth1 - h3-eth0 (IP: 10.0.0.100)
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import Intf

class Router( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( Router, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )
        self.cmd( 'iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE' )

        # Internet connectivity
        Intf( 'eth0', node=self )
        self.cmd( 'dhclient eth0' )

        # Redirection to proxy (h2)
        self.cmd( 'iptables -t nat -A PREROUTING -p tcp --dport 993 -j DNAT --to-destination 10.0.0.100:1030' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        # Flush iptables rules
        self.cmd( 'iptables -F' )
        self.cmd( 'iptables -t nat -F' )

        super( Router, self ).terminate()


class NetworkTopo( Topo ):
    "A Router connecting three IP subnets"

    def build( self, **_opts ):

        defaultIP = '192.168.1.1/8'  # IP address for r0-eth1
        router = self.addNode( 'r0', cls=Router, ip=defaultIP )

        s1, s2, s3 = [ self.addSwitch( s ) for s in 's1', 's2', 's3' ]

        self.addLink( s1, router, intfName2='r0-eth1',
                      params2={ 'ip' : defaultIP } )  # for clarity
        self.addLink( s2, router, intfName2='r0-eth2',
                      params2={ 'ip' : '172.16.0.1/12' } )
        self.addLink( s3, router, intfName2='r0-eth3',
                      params2={ 'ip' : '10.0.0.1/8' } )

        h1 = self.addHost( 'h1', ip='192.168.1.100/8',
                           defaultRoute='via 192.168.1.1' )
        h2 = self.addHost( 'h2', ip='172.16.0.100/12',
                           defaultRoute='via 172.16.0.1' )
        h3 = self.addHost( 'h3', ip='10.0.0.100/8',
                           defaultRoute='via 10.0.0.1' )

        for h, s in [ (h1, s1), (h2, s2), (h3, s3) ]:
            self.addLink( h, s )


def run():
    "Linux router"
    topo = NetworkTopo()
    net = Mininet( topo=topo )  
    
    net.start()

    info( '*** Routing Table on Router:\n' )
    print net[ 'r0' ].cmd( 'route' )
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
