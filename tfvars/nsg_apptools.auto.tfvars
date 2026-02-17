AppTools_nsg_rules = [
  # --- New Rules Added via Automation 2026-02-17 15:57 ---
  {
    name                       = "AppTools_IN_Allow1000"
    description                = "SSH and RDP from internal network"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "VirtualNetwork"
    source_port_range          = "*"
    destination_address_prefix = "10.200.69.64/28"
    destination_port_range     = "22,3389"
  },
  {
    name                       = "AppTools_OUT_Allow1010"
    description                = "Allow Tools to download updates"
    priority                   = 1010
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.200.69.64/28"
    source_port_range          = "*"
    destination_address_prefix = "Internet"
    destination_port_range     = "80,443"
  },
]
