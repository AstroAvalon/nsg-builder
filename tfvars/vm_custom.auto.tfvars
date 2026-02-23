# Example VM customization with multiple data disks and OS selection
# Rename this file to .auto.tfvars to apply it, and fill in the required credentials.
virtual_machines = {
  "app-01" = {
    role           = "app"
    instance       = "01"
    image          = "win22"
    subnet_key     = "AppPrivateLink"
    size           = "Standard_D2s_v3"
    admin_username = "adminuser"
    admin_password = "ChangeMe123!" # Required for Windows
  }
}
