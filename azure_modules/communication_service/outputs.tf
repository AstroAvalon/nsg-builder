output "id" {
  description = "The ID of the Communication Service."
  value       = azurerm_communication_service.this.id
}

output "email_service_id" {
  description = "The ID of the Email Communication Service."
  value       = azurerm_email_communication_service.this.id
}

output "email_domain_id" {
  description = "The ID of the Email Communication Service Domain."
  value       = azurerm_email_communication_service_domain.this.id
}

output "primary_connection_string" {
  description = "The primary connection string of the Communication Service."
  value       = azurerm_communication_service.this.primary_connection_string
  sensitive   = true
}

output "primary_key" {
  description = "The primary key of the Communication Service."
  value       = azurerm_communication_service.this.primary_key
  sensitive   = true
}

output "private_endpoint_ip" {
  description = "The Private IP of the Communication Service Private Endpoint."
  value       = azurerm_private_endpoint.pep.private_service_connection[0].private_ip_address
}
