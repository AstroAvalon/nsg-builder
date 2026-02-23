AppReporting_nsg_rules = [
  # Updated via Automation 2026-02-22 18:04
  {
    name                       = "AppReporting_IN_Allow1400"
    description                = "Report Service HTTP"
    priority                   = 1400
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.1.0.0/24"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "80"
  },
  {
    name                       = "AppReporting_IN_Allow1410"
    description                = "Report Service HTTPS"
    priority                   = 1410
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.1.0.0/24"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "443"
  },
  {
    name                       = "AppReporting_IN_Allow1430"
    description                = "Reporting Port Range"
    priority                   = 1430
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "9000-9100"
  },
  {
    name                       = "AppReporting_IN_Deny1440"
    description                = "Block Ping Public"
    priority                   = 1440
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "Icmp"
    source_address_prefix      = "0.0.0.0/0"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "*"
  },
  {
    name                       = "AppReporting_OUT_Allow1420"
    description                = "Connect to DB"
    priority                   = 1420
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "10.2.0.0/24"
    destination_port_range     = "1433"
  },
]
