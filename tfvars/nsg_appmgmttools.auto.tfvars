AppMGMTTools_nsg_rules = [
  # Updated via Automation 2026-02-22 18:04
  {
    name                       = "AppMGMTTools_IN_Allow1300"
    description                = "RDP from Corp Net"
    priority                   = 1300
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.0.0.0/8"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "3389"
  },
  {
    name                       = "AppMGMTTools_IN_Allow1310"
    description                = "SSH from Corp Net"
    priority                   = 1310
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.0.0.0/8"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "22"
  },
  {
    name                       = "AppMGMTTools_IN_Allow1330"
    description                = "WinRM Access"
    priority                   = 1330
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "192.168.0.0/16"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "5985,5986"
  },
  {
    name                       = "AppMGMTTools_IN_Deny1340"
    description                = "Block NetBIOS"
    priority                   = 1340
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "Udp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "137,138"
  },
  {
    name                       = "AppMGMTTools_IN_Allow1540"
    description                = "Allow SSH Any Protocol"
    priority                   = 1540
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "22"
  },
  {
    name                       = "AppMGMTTools_OUT_Allow1320"
    description                = "Update Downloads"
    priority                   = 1320
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "443"
  },
]
