output "name" {
  description = "The name of the Recovery Services Vault."
  value       = azurerm_recovery_services_vault.this.name
}

output "daily_policy_id" {
  description = "The ID of the Daily Backup Policy."
  value       = azurerm_backup_policy_vm.daily.id
}

output "enhanced_policy_id" {
  description = "The ID of the Enhanced Backup Policy."
  value       = azurerm_backup_policy_vm.enhanced.id
}
