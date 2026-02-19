output "primary_zone_ids" {
  description = "A map of primary Private DNS Zone IDs."
  value       = { for k, v in azurerm_private_dns_zone.primary : k => v.id }
}

output "secondary_zone_ids" {
  description = "A map of secondary Private DNS Zone IDs."
  value       = { for k, v in azurerm_private_dns_zone.secondary : k => v.id }
}
