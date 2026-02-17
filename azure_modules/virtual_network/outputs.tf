output "name" {
  description = "The name of the virtual network."
  value       = azurerm_virtual_network.vnet.name
}

output "id" {
  description = "The virtual network configuration ID."
  value       = azurerm_virtual_network.vnet.id
}

output "resource_group_name" {
  description = "The name of the resource group the virtual network is located in."
  value       = azurerm_virtual_network.vnet.resource_group_name
}