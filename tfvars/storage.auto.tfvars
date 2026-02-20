/*
Best to refer to official documentation on which parameters are accepted for your desired configuration
https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/storage_account

Some common parameters for Premium tier accounts:
- account_kind: BlockBlobStorage, FileStorage
- account_tier: Premium
- account_replication_type: LRS, ZRS

Some common parameters for Standard tier accounts:
- account_kind: StorageV2
- account_tier: Standard
- account_replication_type: LRS, GRS, RAGRS, ZRS

Premium Tier accounts are used in most situations especially for:
- Container persistent storage(FileStorage), which provides NFSv4 enabled containers
- Database backups(BlockBlobStorage)

Other useful information:

- Always enable HTTPS-only traffic for storage accounts that are not NFSv3 enabled, or FileStorage accounts.
- Disable access keys for all storage accounts that do not require them, such as NFS accounts.
- If you need an NFSv3 account, set nfsv3_enabled to true along with hns (heirarchical namespace) to true.
- Access tier should be set to Hot unless your project specifies otherwise.
- BlockBlobStorage does not support access tiers, but the value must still be set. TF will ignore it.
- If you're creating premium accounts, you only need to enable the (private) endpoint that corresponds to the type of storage you're creating.
  - For example, BlockBlobStorage accounts only support the blob endpoint.
- If you're creating standard accounts, enable as many as are required for your use case (enable at least one).
*/

storage_account_config = [
    {
        name                            = "saunquenamefs100"
        account_kind                    = "FileStorage"
        account_tier                    = "Premium"
        account_replication_type        = "LRS"
        access_tier                     = "Hot"
        enable_https_traffic_only       = "false"
        enable_cross_tenant_replication = "true"
        enable_hns                      = false
        nfsv3_enabled                   = false
        disable_access_keys             = false
        create_blob_endpoint            = false
        create_file_endpoint            = true
        create_dfs_endpoint             = false
        create_table_endpoint           = false
        create_queue_endpoint           = false
        containers                     = ["saunquenamefs100"]
    },
    {
        name                            = "saunquename100"
        account_kind                    = "StorageV2"
        account_tier                    = "Standard"
        account_replication_type        = "RAGRS"
        access_tier                     = "Hot"
        enable_https_traffic_only       = "true"
        enable_cross_tenant_replication = "true"
        enable_hns                      = false
        nfsv3_enabled                   = false
        disable_access_keys             = false
        create_blob_endpoint            = true
        create_file_endpoint            = false
        create_dfs_endpoint             = false
        create_table_endpoint           = false
        create_queue_endpoint           = false
        containers                     = ["saunquename100-backups"]
    }
]
