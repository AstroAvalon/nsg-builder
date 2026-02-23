AppTestSavvy_nsg_rules = [
  # Updated via Automation 2026-02-22 18:04
  {
    name                       = "AppTestSavvy_IN_Allow1200"
    description                = "Test Env HTTP"
    priority                   = 1200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "80"
  },
  {
    name                       = "AppTestSavvy_IN_Allow1210"
    description                = "Test Env HTTPS"
    priority                   = 1210
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "443"
  },
  {
    name                       = "AppTestSavvy_IN_Allow1220"
    description                = "SSH from specific host"
    priority                   = 1220
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_address_prefix      = "10.0.0.5"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "22"
  },
  {
    name                       = "AppTestSavvy_IN_Allow1240"
    description                = "DNS Query Test"
    priority                   = 1240
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Udp"
    source_address_prefix      = "10.0.0.0/24"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "53"
  },
  {
    name                       = "AppTestSavvy_IN_Allow1530"
    description                = "Allow Everything Explicit"
    priority                   = 1530
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "*"
  },
  {
    name                       = "AppTestSavvy_OUT_Allow1230"
    description                = "Allow All Outbound for Test"
    priority                   = 1230
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_address_prefix      = "*"
    source_port_range          = "*"
    destination_address_prefix = "*"
    destination_port_range     = "*"
  },
]
