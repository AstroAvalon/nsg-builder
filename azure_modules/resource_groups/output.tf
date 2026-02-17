output "name" {
  description = "The name of the created resource group."
  value       = azurerm_resource_group.resource_group.name
}

output "id" {
  description = "The ID of the created resource group."
  value       = azurerm_resource_group.resource_group.id
}

output "location" {
  description = "The location of the created resource group."
  value       = azurerm_resource_group.resource_group.location
}