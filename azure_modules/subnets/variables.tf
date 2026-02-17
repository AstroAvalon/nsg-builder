variable "resource_group_name" { type = string }
variable "location"            { type = string }
variable "network_name"        { type = string }
variable "subnet_name"         { type = string }
variable "address_space"       { type = string }

# Optional: If null, no NSG is created (e.g. for GatewaySubnet)
variable "security_group_name" { 
  type    = string 
  default = null
}

# List of rules objects
variable "nsg_rules" {
  type = list(object({
    name                       = string
    priority                   = number
    direction                  = string
    access                     = string
    protocol                   = string
    source_port_range          = string
    destination_port_range     = string
    source_address_prefix      = string
    destination_address_prefix = string
  }))
  default = [] 
}