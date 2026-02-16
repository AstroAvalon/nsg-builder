"""
MODULE: Azure NSG Rule Merger
VERSION: 1.2 (Production Ready / AI-Primed)
AUTHOR: DevOps Team
DATE: 2023-10-27

DESCRIPTION:
  Parses an Excel sheet of firewall requests and merges them into Terraform variables (.tfvars).
  It acts as a "Safe Merger" — it reads the existing state from disk to calculate the next
  available priority ID, ensuring no collisions with manually added rules.

ARCHITECTURAL CONSTRAINTS (DO NOT CHANGE WITHOUT APPROVAL):
  1. Source of Truth: The existing .auto.tfvars files in the repo are the primary state.
  2. Naming Convention: Must strictly follow "{Subnet}_{In/Out}_{Allow/Deny}{Priority}".
  3. Priority Logic: Independent counters for Inbound/Outbound. Must preserve existing gaps.
  4. Output Safety: 
     - If existing file found -> Create copy with `_updated` suffix.
     - If new file -> Create clean file (no suffix).

FUTURE ROADMAP (INSTRUCTIONS FOR JULES/AI AGENTS):
  - [ ] Validation: Implement `check_azure_live_state` to query actual Azure NSGs for conflicts.
  - [ ] Parser: Replace regex parsing in `get_next_priorities` with `python-hcl2` library for robustness.
  - [ ] Schema: Add Pydantic validation for the Excel input rows.
"""

import pandas as pd
import re
import os
import glob
import argparse
from datetime import datetime
from typing import Tuple, Dict, Optional, List

# --- CONFIGURATION ---
# AI_NOTE: In the future, these should be loaded from a config.yaml or env vars.
OUTPUT_SUFFIX = "_updated"
START_PRIORITY = 1000
PRIORITY_STEP = 10

def parse_arguments():
    """
    Parses CLI arguments to allow running this script from a central 'tools' repo.
    
    FUTURE INTENT: 
      - Add a `--dry-run` flag that prints planned changes to JSON without writing files.
      - Add a `--validate-only` flag to check Excel syntax.
    """
    parser = argparse.ArgumentParser(description="Merge NSG rules from Excel to Terraform files.")
    parser.add_argument("excel_file", help="Path to the Excel request file")
    parser.add_argument("--repo-root", default=".", help="Root directory of the Terraform repository (default: current dir)")
    return parser.parse_args()

def find_existing_file(subnet_name: str, tfvars_dir: str) -> Optional[str]:
    """
    Locates the source-of-truth file for a given subnet using fuzzy matching.
    
    LOGIC:
      - Normalizes subnet name (removes special chars).
      - Matches against filenames in the tfvars directory.
      - Explicitly ignores files with '_updated' to prevent chaining edits on temporary files.
    """
    safe_name = re.sub(r'[^a-zA-Z0-9]', '', str(subnet_name)).lower()
    
    # AI_NOTE: glob is used here for simple filesystem traversal. 
    # If repo grows >1000 files, switch to os.scandir for performance.
    all_files = glob.glob(os.path.join(tfvars_dir, "*.auto.tfvars"))
    valid_files = [f for f in all_files if OUTPUT_SUFFIX not in f]
    
    for file_path in valid_files:
        filename = os.path.basename(file_path).lower()
        # Check if sanitized subnet name exists in filename (ignoring separators)
        if safe_name in filename.replace('_', '').replace('.', ''):
            return file_path
    return None

def get_next_priorities(file_path: str) -> Tuple[Dict[str, int], str]:
    """
    Scans a text file to determine the next available Priority ID.
    
    AI_IMPROVEMENT_NEEDED: 
      - Currently uses regex on raw text which is brittle if HCL formatting changes.
      - UPGRADE PATH: Implement `python-hcl2` to parse the file into a dict.
    """
    counters = {"IN": START_PRIORITY, "OUT": START_PRIORITY}
    content = ""
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Simple block splitting by "name =" or "{" 
        blocks = content.split("name") 
        
        for block in blocks:
            # Extract Priority
            prio_match = re.search(r'priority\s*=\s*(\d+)', block)
            # Extract Direction
            dir_match = re.search(r'direction\s*=\s*"(\w+)"', block, re.IGNORECASE)
            
            if prio_match and dir_match:
                prio = int(prio_match.group(1))
                direction = dir_match.group(1).upper()
                
                # Logic: Only track priorities in the 1xxx range (User Rules)
                if 1000 <= prio < 2000:
                    short_dir = "IN" if "IN" in direction else "OUT"
                    # Update counter if we found a higher number
                    if prio >= counters[short_dir]:
                        counters[short_dir] = prio + PRIORITY_STEP

        print(f"   ↪ Read Source: {os.path.basename(file_path)}")
        print(f"   ↪ Detected Max Priorities -> Inbound: {counters['IN']-10} | Outbound: {counters['OUT']-10}")
        
    except Exception as e:
        print(f"   ⚠️  CRITICAL: Could not parse existing file {file_path}: {e}")
        
    return counters, content

def check_azure_live_state(subnet_name: str, subscription_id: str):
    """
    FUTURE FEATURE STUB (Do not remove):
    1. Authenticate using Azure CLI credentials.
    2. Query the actual NSG in Azure to get current rules.
    3. Return a list of 'taken' priorities to avoid conflicts with manual portal changes.
    """
    # JULES_TODO: Implement using azure-identity and azure-mgmt-network libraries
    pass

def merge_nsg_rules(excel_path: str, repo_root: str):
    # Construct paths
    tfvars_dir = os.path.join(repo_root, "tfvars")
    if not os.path.exists(tfvars_dir):
        print(f"❌ Error: Could not find 'tfvars' folder at: {tfvars_dir}")
        return

    # Load Excel
    try:
        df = pd.read_excel(excel_path, dtype=str)
        df.columns = df.columns.str.strip()
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    # API Mapping for consistent casing
    api_map = {
        "TCP": "Tcp", "UDP": "Udp", "ICMP": "Icmp", "ANY": "*", "*": "*",
        "INBOUND": "Inbound", "OUTBOUND": "Outbound",
        "ALLOW": "Allow", "DENY": "Deny"
    }

    # --- Helper Functions (Sanitization) ---
    def clean_port(val: str) -> str:
        """
        Fixes common Excel typos in port lists.
        Example: '80. 443' -> '80,443'
        """
        if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]: return "*"
        
        # Regex to find dots between numbers (handling spaces)
        cleaned = re.sub(r'(\d)\s*\.\s*(\d)', r'\1,\2', str(val))
        return re.sub(r'\s+', '', cleaned).replace(',,', ',').strip(',')

    def clean_ip(val: str) -> str:
        """Removes spaces from IP lists."""
        if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]: return "*"
        return re.sub(r'\s+', '', str(val)).strip(',')

    # --- Main Processing Loop ---
    grouped = df.groupby('Azure Subnet Name')

    for subnet_raw, rules in grouped:
        if pd.isna(subnet_raw): continue
        
        print(f"\nProcessing Subnet: {subnet_raw}")
        
        # 1. Identify Source File
        existing_file = find_existing_file(subnet_raw, tfvars_dir)
        
        prio_counters = {"IN": START_PRIORITY, "OUT": START_PRIORITY}
        base_content = ""
        new_filename = ""
        
        if existing_file:
            # --- EXISTING FILE LOGIC (Read -> Append -> Safe Save) ---
            prio_counters, old_content = get_next_priorities(existing_file)
            
            # Strip the last closing bracket ']' to prepare for append
            last_bracket_idx = old_content.rfind(']')
            if last_bracket_idx != -1:
                base_content = old_content[:last_bracket_idx]
            else:
                base_content = old_content 
            
            # Construct SAFE filename (append _updated)
            base_name = os.path.basename(existing_file)
            name_part, ext_part = os.path.splitext(base_name)
            # Handle .auto.tfvars double extension
            if name_part.endswith(".auto"):
                name_part = name_part.replace(".auto", "")
                ext = ".auto.tfvars"
            else:
                ext = ".tfvars"
                
            new_filename = os.path.join(tfvars_dir, f"{name_part}{OUTPUT_SUFFIX}{ext}")
            print(f"   ↪ Found existing file. Creating SAFE update copy: {os.path.basename(new_filename)}")
            
        else:
            # --- NEW FILE LOGIC (Clean Creation) ---
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', str(subnet_raw))
            # AI_NOTE: New files strictly follow `nsg_{name}.auto.tfvars` naming convention.
            new_filename = os.path.join(tfvars_dir, f"nsg_{clean_name.lower()}.auto.tfvars")
            base_content = f"{clean_name}_nsg_rules = ["
            print(f"   ↪ No source file found. Creating NEW file: {os.path.basename(new_filename)}")

        # 2. Generate New Rules Block
        # Adding a timestamped comment block for auditability
        new_rules_hcl = f"\n  # --- New Rules Added via Automation {datetime.now().strftime('%Y-%m-%d %H:%M')} ---"
        
        for _, row in rules.iterrows():
            raw_dir = str(row['Direction']).upper().strip()
            dir_short = "IN" if "IN" in raw_dir else "OUT"
            
            # Priority Calculation
            try:
                if pd.isna(row['Priority']) or str(row['Priority']).strip() == "":
                    prio_val = prio_counters[dir_short]
                    prio_counters[dir_short] += PRIORITY_STEP
                else:
                    prio_val = int(float(row['Priority']))
            except (ValueError, TypeError):
                prio_val = prio_counters[dir_short]
                prio_counters[dir_short] += PRIORITY_STEP

            # Map inputs to Azure API constraints
            dir_api = api_map.get(raw_dir, "Inbound")
            access_api = api_map.get(str(row['Access']).upper().strip(), "Allow")
            proto_api = api_map.get(str(row['Protocol']).upper().strip(), "Tcp")
            clean_subnet_name = re.sub(r'[^a-zA-Z0-9]', '', str(subnet_raw))
            
            # Generate Rule Name (Strict Convention)
            rule_name = f"{clean_subnet_name}_{dir_short}_{access_api}{prio_val}"
            
            new_rules_hcl += f"""
  {{
    name                       = "{rule_name}"
    description                = "{str(row['Description'])[:100]}"
    priority                   = {prio_val}
    direction                  = "{dir_api}"
    access                     = "{access_api}"
    protocol                   = "{proto_api}"
    source_address_prefix      = "{clean_ip(row['Source'])}"
    source_port_range          = "*"
    destination_address_prefix = "{clean_ip(row['Destination'])}"
    destination_port_range     = "{clean_port(row['Destination Port'])}"
  }},"""

        # 3. Assemble and Write
        final_content = base_content.rstrip() + new_rules_hcl + "\n]\n"
        
        os.makedirs(os.path.dirname(new_filename), exist_ok=True)
        
        with open(new_filename, "w") as f:
            f.write(final_content)
            
        print(f"   ✅ SUCCESS: Wrote to -> {new_filename}")

if __name__ == "__main__":
    args = parse_arguments()
    merge_nsg_rules(args.excel_file, args.repo_root)