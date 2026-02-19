output "name" {
  description = "The name of the Key Vault."
  value       = azurerm_key_vault.kv.name
}

output "id" {
  description = "The ID of the Key Vault."
  value       = azurerm_key_vault.kv.id
}

output "private_endpoint_ip" {
  description = "The private IP address of the Key Vault Private Endpoint."
  value       = azurerm_private_endpoint.pe.private_service_connection[0].private_ip_address
}
