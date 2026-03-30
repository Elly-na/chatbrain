"""
Cisco Command Configuration Database
Contains all device configurations and command templates
"""

DEVICE_CONFIGS = {
    'S1': {
        'type': 'switch',
        'hostname': 'S1',
        'interfaces': {
            'fastEthernet0/1': {
                'mode': 'access',
                'status': 'no shutdown'
            },
            'fastEthernet1/1': {
                'mode': 'access',
                'status': 'no shutdown'
            }
        },
        'full_config': '''enable
configure terminal
hostname S1
interface fastEthernet0/1
switchport mode access
no shutdown
interface fastEthernet1/1
switchport mode access
no shutdown
exit'''
    },
    
    'S2': {
        'type': 'switch',
        'hostname': 'S2',
        'interfaces': {
            'fastEthernet0/1': {
                'mode': 'access',
                'status': 'no shutdown'
            },
            'fastEthernet1/1': {
                'mode': 'access',
                'status': 'no shutdown'
            }
        },
        'full_config': '''enable
configure terminal
hostname S2
interface fastEthernet0/1
switchport mode access
no shutdown
interface fastEthernet1/1
switchport mode access
no shutdown
exit'''
    },
    
    'R1': {
        'type': 'router',
        'hostname': 'R1',
        'interfaces': {
            'gigabitEthernet0/0': {
                'ip': '192.168.10.1',
                'mask': '255.255.255.0',
                'status': 'no shutdown'
            },
            'serial0/3/0': {
                'ip': '10.10.10.1',
                'mask': '255.255.255.252',
                'status': 'no shutdown'
            }
        },
        'routes': ['ip route 192.168.20.0 255.255.255.0 10.10.10.2'],
        'rip': {
            'version': 2,
            'networks': ['192.168.10.0', '10.10.10.0']
        },
        'full_config': '''enable
configure terminal
hostname R1
interface gigabitEthernet0/0
ip address 192.168.10.1 255.255.255.0
no shutdown
interface serial0/3/0
ip address 10.10.10.1 255.255.255.252
no shutdown
ip route 192.168.20.0 255.255.255.0 10.10.10.2
exit''',
        'rip_config': '''enable
configure terminal
router rip
version 2
no auto-summary
network 192.168.10.0
network 10.10.10.0
end
write memory'''
    },
    
    'R2': {
        'type': 'router',
        'hostname': 'R2',
        'interfaces': {
            'serial0/2/0': {
                'ip': '10.10.10.2',
                'mask': '255.255.255.252',
                'status': 'no shutdown'
            },
            'gigabitEthernet0/0': {
                'ip': '192.168.20.1',
                'mask': '255.255.255.0',
                'status': 'no shutdown'
            }
        },
        'routes': ['ip route 192.168.10.0 255.255.255.0 10.10.10.1'],
        'rip': {
            'version': 2,
            'networks': ['192.168.20.0', '10.10.10.0']
        },
        'full_config': '''enable
configure terminal
hostname R2
interface serial0/2/0
ip address 10.10.10.2 255.255.255.252
no shutdown
interface gigabitEthernet0/0
ip address 192.168.20.1 255.255.255.0
no shutdown
ip route 192.168.10.0 255.255.255.0 10.10.10.1
exit''',
        'rip_config': '''enable
configure terminal
router rip
version 2
no auto-summary
network 192.168.20.0
network 10.10.10.0
end
write memory'''
    }
}

COMMAND_CATEGORIES = {
    'basic': {
        'name': 'Basic Configuration',
        'commands': [
            {
                'name': 'Set Hostname',
                'example': 'set hostname to R1',
                'syntax': 'hostname [NAME]',
                'template': '''enable
configure terminal
hostname {hostname}
exit'''
            },
            {
                'name': 'Enable Interface',
                'example': 'enable interface gigabitEthernet0/0',
                'syntax': 'no shutdown',
                'template': '''enable
configure terminal
interface {interface}
no shutdown
exit'''
            },
            {
                'name': 'Disable Interface',
                'example': 'disable interface gigabitEthernet0/0',
                'syntax': 'shutdown',
                'template': '''enable
configure terminal
interface {interface}
shutdown
exit'''
            }
        ]
    },
    
    'ip': {
        'name': 'IP Configuration',
        'commands': [
            {
                'name': 'Configure IP Address',
                'example': 'configure ip 192.168.1.1 on gigabitEthernet0/0',
                'syntax': 'ip address [IP] [MASK]',
                'template': '''enable
configure terminal
interface {interface}
ip address {ip} {mask}
no shutdown
exit'''
            },
            {
                'name': 'Show IP Interface Brief',
                'example': 'show ip interface brief',
                'syntax': 'show ip interface brief',
                'template': 'show ip interface brief'
            },
            {
                'name': 'Show IP Route',
                'example': 'show ip route',
                'syntax': 'show ip route',
                'template': 'show ip route'
            }
        ]
    },
    
    'routing': {
        'name': 'Routing Configuration',
        'commands': [
            {
                'name': 'Static Route',
                'example': 'add route to network 192.168.20.0 via 10.10.10.2',
                'syntax': 'ip route [NETWORK] [MASK] [NEXT-HOP]',
                'template': '''enable
configure terminal
ip route {network} {mask} {nexthop}
exit'''
            },
            {
                'name': 'RIP Routing',
                'example': 'configure RIP on R1',
                'syntax': 'router rip',
                'template': '''enable
configure terminal
router rip
version 2
no auto-summary
network {network}
end
write memory'''
            }
        ]
    },
    
    'switch': {
        'name': 'Switch Configuration',
        'commands': [
            {
                'name': 'Switchport Mode Access',
                'example': 'configure switchport mode access on fastEthernet0/1',
                'syntax': 'switchport mode access',
                'template': '''enable
configure terminal
interface {interface}
switchport mode access
no shutdown
exit'''
            },
            {
                'name': 'Switchport Mode Trunk',
                'example': 'configure switchport mode trunk on fastEthernet0/1',
                'syntax': 'switchport mode trunk',
                'template': '''enable
configure terminal
interface {interface}
switchport mode trunk
no shutdown
exit'''
            }
        ]
    },
    
    'security': {
        'name': 'Security Configuration',
        'commands': [
            {
                'name': 'Enable Password',
                'example': 'set enable password to cisco123',
                'syntax': 'enable password [PASSWORD]',
                'template': '''enable
configure terminal
enable password {password}
exit'''
            },
            {
                'name': 'Enable Secret',
                'example': 'set enable secret to cisco123',
                'syntax': 'enable secret [PASSWORD]',
                'template': '''enable
configure terminal
enable secret {password}
exit'''
            },
            {
                'name': 'Console Password',
                'example': 'set console password to cisco123',
                'syntax': 'line console 0 / password [PASSWORD]',
                'template': '''enable
configure terminal
line console 0
password {password}
login
exit'''
            }
        ]
    },
    
    'show': {
        'name': 'Show Commands',
        'commands': [
            {
                'name': 'Show Running Config',
                'example': 'show running config',
                'syntax': 'show running-config',
                'template': 'show running-config'
            },
            {
                'name': 'Show Version',
                'example': 'show version',
                'syntax': 'show version',
                'template': 'show version'
            },
            {
                'name': 'Show Interfaces',
                'example': 'show interfaces',
                'syntax': 'show interfaces',
                'template': 'show interfaces'
            }
        ]
    },
    
    'rip': {
        'name': 'RIP Configuration',
        'commands': [
            {
                'name': 'Enable RIP',
                'example': 'enable RIP on R1',
                'syntax': 'router rip',
                'template': '''enable
configure terminal
router rip
version 2
no auto-summary
network {network}
end
write memory'''
            },
            {
                'name': 'Add RIP Network',
                'example': 'add RIP network 192.168.1.0',
                'syntax': 'network [NETWORK]',
                'template': '''enable
configure terminal
router rip
network {network}
end
write memory'''
            },
            {
                'name': 'Show RIP Routes',
                'example': 'show RIP routes',
                'syntax': 'show ip rip database',
                'template': 'show ip rip database'
            }
        ]
    }
}

HELP_TEXT = {
    'all': '''🔧 CISCO COMMAND - ALL COMMANDS

💡 Basic Configuration
    -help basic
    
💡 Ip Configuration 
   -help ip
   
💡 Routing
   -help routing
   
💡 Switch Configuration
   -help switch
   
💡 Security
   -help security
   
💡 Show Commands
    -help show
    
💡 Device Configuration
    -show device [device_name]

💡 Type "help [category]" for specific help
   Categories: basic, ip, routing, switch, security, show, rip''',
    
    'basic': '''📌 BASIC CONFIGURATION COMMANDS:

1️⃣ SET HOSTNAME
   Example: "set hostname to R1"
   Command: hostname [NAME]

2️⃣ ENABLE INTERFACE
   Example: "enable interface gigabitEthernet0/0"
   Command: no shutdown

3️⃣ DISABLE INTERFACE
   Example: "disable interface gigabitEthernet0/0"
   Command: shutdown''',
    
    'ip': '''📌 IP CONFIGURATION COMMANDS:

1️⃣ CONFIGURE IP ADDRESS
   Example: "configure ip 192.168.1.1 on gigabitEthernet0/0"
   Command: ip address [IP] [MASK]

2️⃣ SHOW IP BRIEF
   Example: "show ip interface brief"
   Command: show ip interface brief

3️⃣ SHOW IP ROUTE
   Example: "show ip route"
   Command: show ip route''',
    
    'routing': '''📌 ROUTING CONFIGURATION COMMANDS:

1️⃣ STATIC ROUTE
   Example: "add route to network 192.168.20.0 via 10.10.10.2"
   Command: ip route [NETWORK] [MASK] [NEXT-HOP]

2️⃣ RIP ROUTING
   Example: "configure RIP on R1"
   Command: router rip / version 2 / network [NETWORK]''',
    
    'switch': '''📌 SWITCH CONFIGURATION COMMANDS:

1️⃣ SWITCHPORT ACCESS MODE
   Example: "configure switchport mode access on fastEthernet0/1"
   Command: switchport mode access

2️⃣ SWITCHPORT TRUNK MODE
   Example: "configure switchport mode trunk on fastEthernet0/1"
   Command: switchport mode trunk''',
    
    'security': '''📌 SECURITY CONFIGURATION COMMANDS:

1️⃣ ENABLE PASSWORD
   Example: "set enable password to cisco123"
   Command: enable password [PASSWORD]

2️⃣ ENABLE SECRET (Encrypted)
   Example: "set enable secret to cisco123"
   Command: enable secret [PASSWORD]

3️⃣ CONSOLE PASSWORD
   Example: "set console password to cisco123"
   Command: line console 0 / password [PASSWORD] / login''',
    
    'show': '''📌 SHOW COMMANDS:

1️⃣ SHOW RUNNING CONFIG
   Example: "show running config"
   Command: show running-config

2️⃣ SHOW VERSION
   Example: "show version"
   Command: show version

3️⃣ SHOW INTERFACES
   Example: "show interfaces"
   Command: show interfaces''',
    
    'rip': '''📌 RIP CONFIGURATION COMMANDS:

1️⃣ ENABLE RIP
   Example: "enable RIP on R1"
   Command: router rip / version 2 / network [NETWORK]

2️⃣ ADD RIP NETWORK
   Example: "add RIP network 192.168.1.0"
   Command: network [NETWORK]

3️⃣ SHOW RIP ROUTES
   Example: "show RIP routes"
   Command: show ip rip database'''
}