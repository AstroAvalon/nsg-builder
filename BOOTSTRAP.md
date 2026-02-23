# Terraform & Pipeline Bootstrap Guide

This guide explains how to initialize the infrastructure and set up the Azure DevOps pipeline.

## Prerequisites

1.  **Azure Subscription**: Access to create resources.
2.  **Azure CLI**: Installed and logged in (`az login`).
3.  **Terraform**: Installed locally.

## Step 1: Initial Deployment (Local)

Since the Terraform Backend (Storage Account) and Key Vault are managed by this same Terraform code, we must first deploy them locally before we can use the remote backend.

1.  **Comment out the Backend Configuration** in `main.tf`:
    ```hcl
    # backend "azurerm" {}
    ```

2.  **Initialize Terraform Locally**:
    ```bash
    terraform init
    ```

3.  **Apply the Configuration**:
    This will create the Resource Groups, Storage Account (for backend), Key Vault, and generate the initial secrets.
    ```bash
    terraform apply
    ```
    *Note the outputs for:*
    *   `backend_resource_group_name`
    *   `backend_storage_account_name`
    *   `backend_container_name`

## Step 2: Migrate State to Remote Backend

1.  **Uncomment the Backend Configuration** in `main.tf`:
    ```hcl
    backend "azurerm" {}
    ```

2.  **Initialize Migration**:
    Replace the placeholders with the actual values from the previous step's output.
    ```bash
    terraform init \
      -backend-config="resource_group_name=<backend_rg_name>" \
      -backend-config="storage_account_name=<backend_sa_name>" \
      -backend-config="container_name=tfstate" \
      -backend-config="key=terraform.tfstate"
    ```
    Type `yes` when prompted to copy the state file.

## Step 3: Configure Azure DevOps

1.  **Create a Service Connection**:
    *   Name: `azure-connection` (or update `azure-pipelines.yml` with your name).
    *   Type: Azure Resource Manager (Workload Identity federation recommended).

2.  **Create a Variable Group**:
    *   Name: `terraform-secrets`
    *   Link to the Key Vault created in Step 1.
    *   **Add Non-KeyVault Variables**:
        *   `backend_rg`: (Value from Step 1 output)
        *   `backend_sa`: (Value from Step 1 output)
        *   `backend_container`: `tfstate`
        *   `backend_key`: `terraform.tfstate`
        *   `destroy_env`: `false`
    *   **Map KeyVault Secrets**:
        *   Select `vm-admin-password` and verify it is mapped.

3.  **Run the Pipeline**:
    *   Commit and push your changes.
    *   The pipeline should trigger and run `Plan`.
    *   Review and approve the `Apply` stage.

## Common Variables

*   **VM Admin Password**: Stored in Key Vault as `vm-admin-password`. The pipeline automatically injects this into Terraform as `var.common_admin_password`.
*   **Destroying Environment**: To destroy the environment via pipeline, update the variable `destroy_env` to `true` in the Variable Group or at queue time.
