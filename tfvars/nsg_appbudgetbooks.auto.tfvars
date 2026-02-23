AppBudgetBooks_nsg_rules = [
  # Updated via Automation 2026-02-22 18:04
  {
    name                       = "AppBudgetBooks_IN_Allow1100"
    description                = "Web Interface"
    priority                   = 1100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "8080"
  },
  {
    name                       = "AppBudgetBooks_IN_Allow1110"
    description                = "Secure Web Interface"
    priority                   = 1110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "8443"
  },
  {
    name                       = "AppBudgetBooks_IN_Deny1130"
    description                = "Block Internet Inbound"
    priority                   = 1130
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_address_prefix      = "Internet"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "*"
  },
  {
    name                       = "AppBudgetBooks_IN_Allow1140"
    description                = "Allow Ping Internal"
    priority                   = 1140
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Icmp"
    source_address_prefix      = "10.0.0.0/16"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "*"
  },
  {
    name                       = "AppBudgetBooks_OUT_Allow1120"
    description                = "RDP to Management"
    priority                   = 1120
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "10.5.0.0/24"
    destination_port_range     = "3389"
  },
  {
    name                       = "AppBudgetBooks_OUT_Deny1520"
    description                = "Block Google DNS"
    priority                   = 1520
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "Udp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "8.8.8.8"
    destination_port_range     = "53"
  },
]
