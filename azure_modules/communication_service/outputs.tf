output "id" {
  description = "The ID of the Communication Service."
  value       = azurerm_communication_service.acs.id
}

output "email_service_id" {
  description = "The ID of the Email Communication Service."
  value       = azurerm_email_communication_service.ecs.id
}

output "email_domain_id" {
  description = "The ID of the Email Communication Service Domain."
  value       = azurerm_email_communication_service_domain.domain.id
}

output "primary_connection_string" {
  description = "The primary connection string of the Communication Service."
  value       = azurerm_communication_service.acs.primary_connection_string
  sensitive   = true
}

output "primary_key" {
  description = "The primary key of the Communication Service."
  value       = azurerm_communication_service.acs.primary_key
  sensitive   = true
}
