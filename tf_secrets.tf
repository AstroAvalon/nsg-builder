# Generate a secure password for VM administration
resource "random_password" "vm_admin" {
  length           = 16
  special          = true
  override_special = "!@#$%^&*()-_=+[]{}<>:?"
}

# Grant the current executing principal access to manage secrets in the Key Vault
# This is necessary for Terraform to create the secrets below.
resource "azurerm_role_assignment" "kv_secrets_officer" {
  scope                = module.keyvault.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Wait for RBAC propagation to avoid 403 errors when creating secrets
resource "time_sleep" "wait_for_rbac" {
  create_duration = "30s"
  depends_on      = [azurerm_role_assignment.kv_secrets_officer]
}

# Store the VM Admin Password in Key Vault
resource "azurerm_key_vault_secret" "vm_admin_password" {
  name         = "vm-admin-password"
  value        = random_password.vm_admin.result
  key_vault_id = module.keyvault.id
  content_type = "password"

  depends_on = [
    time_sleep.wait_for_rbac
  ]
}

# Store the Domain Join Password (placeholder example)
resource "random_password" "domain_join" {
  length           = 16
  special          = true
  override_special = "!@#$%^&*()-_=+[]{}<>:?"
}

resource "azurerm_key_vault_secret" "domain_join_password" {
  name         = "domain-join-password"
  value        = random_password.domain_join.result
  key_vault_id = module.keyvault.id
  content_type = "password"

  depends_on = [
    time_sleep.wait_for_rbac
  ]
}

# Store the Terraform Service Principal Client ID (if known, or placeholder)
# For now, we'll store the current client ID as an example
resource "azurerm_key_vault_secret" "tf_client_id" {
  name         = "tf-client-id"
  value        = data.azurerm_client_config.current.client_id
  key_vault_id = module.keyvault.id

  depends_on = [
    time_sleep.wait_for_rbac
  ]
}
