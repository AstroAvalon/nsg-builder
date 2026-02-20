# Azure NSG Rule Automation

This tool automates the management of Azure Network Security Group (NSG) rules by parsing Excel requests and merging them into Terraform variable files (`.tfvars`). It ensures safe updates, prevents conflicts, and maintains consistency across your infrastructure code.

## Key Features

- **Safe Merging**: Scans existing `.tfvars` to determine available priority IDs and prevents collisions.
- **Output Safety**: Never overwrites existing files directly; updates are saved with an `_updated` suffix.
- **Validation**: Cleans input data (e.g., ports, IPs) and maps them to Azure API constraints.
- **Base Rules**: Supports applying a standard set of rules across all subnets.

## Dependencies

Requires Python 3 and the following packages:

```bash
pip install pandas openpyxl
```

## Usage

### Merging Rules

To merge rules from an Excel request file:

```bash
python nsg_merger.py nsg_request.xlsx
```

This will read the requests, check for existing rules in `tfvars/`, and generate new or updated `.tfvars` files.

**Options:**

- `--base-rules <file>`: Apply a set of base rules to all subnets.
- `--repo-root <path>`: Specify the root directory of the repository (defaults to current).

### Validation

To validate that the rules in your Excel file match the current Terraform configuration:

```bash
python validator.py nsg_request.xlsx
```

This compares the requested rules against the `.tfvars` files to ensure all requests are present and correctly configured.

## File Structure

- `nsg_merger.py`: Main script for processing Excel requests.
- `validator.py`: Validates that requests exist in the code.
- `azure_helper.py`: Shared logic for parsing HCL and Azure interactions.
- `tfvars/`: Contains the Terraform variable files for NSG rules.

## Constraints

1.  **Source of Truth**: The `.tfvars` files in the repo are the primary state.
2.  **Naming Convention**: Rules follow `{Subnet}_{In/Out}_{Allow/Deny}{Priority}`.
3.  **Priorities**: Inbound and Outbound priorities are tracked separately.
4.  **No Direct Overwrites**: Updates are always saved as `_updated` files for manual review before replacing the original.
