# Azure NSG Rule Merger & Automation

This tool automates the process of managing Azure Network Security Group (NSG) rules by parsing Excel requests and merging them into Terraform variable files (`.tfvars`). It ensures safety, prevents conflicts, and maintains consistency across your infrastructure as code.

## Description

The core script, `nsg_merger.py`, reads firewall rule requests from an Excel spreadsheet and updates the corresponding `.tfvars` files. It acts as a "Safe Merger" by:
1.  **Reading Existing State**: It scans existing `.tfvars` files to determine the next available priority ID, ensuring no collisions with manually added rules.
2.  **Safe Output**: If an existing file is found, it creates a copy with an `_updated` suffix to prevent accidental overwrites. New files are created cleanly.
3.  **Validation**: It cleans up input data (e.g., fixing port/IP formatting) and maps Excel inputs to Azure API constraints.

## Dependencies

To run this tool, you need Python installed along with the following packages:

*   `pandas`
*   `openpyxl` (for reading Excel files)

You can install them via pip:

```bash
pip install pandas openpyxl
```

## Usage

### 1. Prepare your Request File
Ensure your Excel file (e.g., `nsg_request.xlsx`) follows the required format with columns for:
*   Azure Subnet Name
*   Priority (optional, auto-calculated if empty)
*   Direction (Inbound/Outbound)
*   Access (Allow/Deny)
*   Source / Destination (IPs or CIDRs)
*   Protocol (TCP, UDP, ICMP, *)
*   Destination Port
*   Description

### 2. Run the Merger Script
Execute the script from the command line, providing the path to your Excel file:

```bash
python nsg_merger.py nsg_request.xlsx
```

To specify the root of the Terraform repository (defaults to current directory):

```bash
python nsg_merger.py nsg_request.xlsx --repo-root /path/to/repo
```

### 3. Review Output
*   **New Files**: Created as `tfvars/nsg_<subnet_name>.auto.tfvars`.
*   **Updated Files**: Created as `tfvars/<original_filename>_updated.auto.tfvars`.

Review the generated files in the `tfvars/` directory before committing them to your repository.

## Workflow

1.  **Request**: Users submit firewall rule requests via an Excel template.
2.  **Processing**: `nsg_merger.py` reads the Excel file.
3.  **State Check**: The script checks `tfvars/` for existing rules for the specified subnets.
4.  **Generation**:
    *   Priorities are calculated based on existing rules (starting from 1000).
    *   Rules are formatted into HCL (HashiCorp Configuration Language).
    *   New `.tfvars` files are generated or updated.
5.  **Validation**: `validator.py` can be used to generate a `processing_report.json` detailing transformations and errors.

## File Structure

*   `nsg_merger.py`: The main script for merging Excel rules into `.tfvars`.
*   `validator.py`: A supplementary script for validating Excel data and generating a detailed JSON report (`processing_report.json`).
*   `tfvars/`: Directory containing the Terraform variable files.
*   `nsg_request.xlsx`: Example Excel file containing rule requests.
*   `processing_report.json`: Output report from `validator.py`.

## Architectural Constraints

The following constraints are enforced to ensure stability and consistency:

1.  **Source of Truth**: The existing `.auto.tfvars` files in the repo are the primary state.
2.  **Naming Convention**: Rules strictly follow `{Subnet}_{In/Out}_{Allow/Deny}{Priority}`.
3.  **Priority Logic**: Independent counters for Inbound/Outbound rules are maintained to preserve gaps.
4.  **Output Safety**: Existing files are never overwritten directly; updates are saved with an `_updated` suffix.

## Future Roadmap

*   **Live Validation**: Implement checks against actual Azure NSG state using Azure CLI/SDK.
*   **Robust Parsing**: Replace regex parsing with `python-hcl2` for better HCL handling.
*   **Schema Validation**: Add Pydantic validation for Excel input rows.
