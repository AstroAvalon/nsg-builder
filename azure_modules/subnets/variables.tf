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

# Service Endpoints
variable "service_endpoints" {
  description = "A list of service endpoints to associate with the subnet."
  type        = list(string)
  default     = []
}

# Private Endpoint Network Policies
variable "private_endpoint_network_policies" {
  description = "Enable or disable network policies for private endpoints on the subnet. Options: Enabled, Disabled."
  type        = string
  default     = "Enabled"
}

# Subnet Delegations
variable "aks_delegation" {
  description = "Enable delegation for Azure Kubernetes Service (AKS)."
  type        = bool
  default     = false
}

variable "databricks_delegation" {
  description = "Enable delegation for Azure Databricks."
  type        = bool
  default     = false
}

variable "postgres_delegation" {
  description = "Enable delegation for PostgreSQL Flexible Server."
  type        = bool
  default     = false
}
