import argparse
import pandas as pd
import re
import json
import sys
from datetime import datetime


def generate_nsg_tfvars(excel_path, start_priority=1000, dry_run=False):
    # Initialize the "Agent Report"
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "files_generated": [],
        "errors": [],
        "transformations": [],
        "summary": {"total_rules": 0, "fixed_typos": 0},
    }

    # 1. Load and Validate Excel
    try:
        df = pd.read_excel(excel_path, dtype=str)
    except Exception as e:
        report["status"] = "failed"
        report["errors"].append(f"Could not read file: {str(e)}")
        return json.dumps(report, indent=2)

    df.columns = df.columns.str.strip()

    required_cols = [
        "Azure Subnet Name",
        "Priority",
        "Direction",
        "Access",
        "Source",
        "Destination",
        "Protocol",
        "Destination Port",
        "Description",
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        report["status"] = "failed"
        report["errors"].append(f"Missing columns: {missing_cols}")
        return json.dumps(report, indent=2)

    # API Mapping
    api_map = {
        "TCP": "Tcp",
        "UDP": "Udp",
        "ICMP": "Icmp",
        "ANY": "*",
        "*": "*",
        "INBOUND": "Inbound",
        "OUTBOUND": "Outbound",
        "ALLOW": "Allow",
        "DENY": "Deny",
    }

    # Helper Functions with Structured Logging
    def clean_port_list(val, row_idx, rule_desc):
        if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]:
            return "*"

        original = str(val)
        # Fix: Dots between numbers
        cleaned = re.sub(r"(\d)\s*\.\s*(\d)", r"\1,\2", original)

        # Log transformation if needed
        if cleaned != original:
            report["transformations"].append(
                {
                    "row": row_idx,
                    "rule": rule_desc,
                    "field": "Destination Port",
                    "original": original,
                    "fixed": cleaned,
                    "type": "typo_fix",
                }
            )
            report["summary"]["fixed_typos"] += 1

        final = re.sub(r"\s+", "", cleaned).replace(",,", ",").strip(",")
        return final

    def clean_ip_list(val):
        if pd.isna(val) or str(val).strip().lower() in ["", "any", "all", "*"]:
            return "*"
        return re.sub(r"\s+", "", str(val)).strip(",")

    # Processing Logic
    grouped = df.groupby("Azure Subnet Name")

    for subnet_raw, rules in grouped:
        if pd.isna(subnet_raw):
            continue

        clean_subnet = re.sub(r"[^a-zA-Z0-9]", "", str(subnet_raw))
        filename = f"{clean_subnet}_nsg_rules.tfvars"
        var_name = f"{clean_subnet}_nsg_rules"

        prio_counters = {"IN": start_priority, "OUT": start_priority}
        hcl_output = [f"{var_name} = ["]

        for idx, row in rules.iterrows():
            report["summary"]["total_rules"] += 1
            excel_row_num = idx + 2

            # 1. Direction & Casing
            raw_dir = str(row["Direction"]).upper().strip()
            dir_short = "IN" if "IN" in raw_dir else "OUT"
            direction_api = api_map.get(raw_dir, "Inbound")

            if raw_dir not in ["INBOUND", "OUTBOUND", "IN", "OUT"]:
                report["transformations"].append(
                    {
                        "row": excel_row_num,
                        "field": "Direction",
                        "original": row["Direction"],
                        "fixed": direction_api,
                        "type": "standardization",
                    }
                )

            # 2. Priority Logic
            prio_val = 0
            try:
                if pd.isna(row["Priority"]) or str(row["Priority"]).strip() == "":
                    prio_val = prio_counters[dir_short]
                    prio_counters[dir_short] += 10
                    # We don't log every auto-priority as a "fix", but we could.
                else:
                    prio_val = int(float(row["Priority"]))
            except:
                prio_val = prio_counters[dir_short]
                prio_counters[dir_short] += 10
                report["transformations"].append(
                    {
                        "row": excel_row_num,
                        "field": "Priority",
                        "original": str(row["Priority"]),
                        "fixed": prio_val,
                        "type": "invalid_format_fix",
                    }
                )

            # 3. Protocol & Access
            raw_proto = str(row["Protocol"]).upper().strip()
            proto_api = api_map.get(raw_proto, "Tcp")
            access_api = api_map.get(str(row["Access"]).upper().strip(), "Allow")

            # 4. Cleaning
            clean_dest_port = clean_port_list(
                row["Destination Port"], excel_row_num, str(row["Description"])[:20]
            )
            clean_source_addr = clean_ip_list(row["Source"])
            clean_dest_addr = clean_ip_list(row["Destination"])

            # 5. Build HCL
            rule_name = f"{clean_subnet}_{dir_short}_{access_api}{prio_val}"

            rule_block = f"""  {{
    name                       = "{rule_name}"
    description                = "{str(row['Description'])[:100]}"
    priority                   = {prio_val}
    direction                  = "{direction_api}"
    access                     = "{access_api}"
    protocol                   = "{proto_api}"
    source_address_prefix      = "{clean_source_addr}"
    source_port_range          = "*"
    destination_address_prefix = "{clean_dest_addr}"
    destination_port_range     = "{clean_dest_port}"
  }},"""
            hcl_output.append(rule_block)

        hcl_output.append("]")

        if not dry_run:
            with open(filename, "w") as f:
                f.write("\n".join(hcl_output))
            report["files_generated"].append(filename)

    report["status"] = "success"

    # Dump report to JSON file for Audit/Agent
    with open("processing_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return json.dumps(report, indent=2)


def parse_arguments():
    """
    Parses CLI arguments for the NSG tfvars generator.
    """
    parser = argparse.ArgumentParser(description="Generate NSG tfvars from Excel.")
    parser.add_argument("excel_path", help="Path to the Excel request file")
    parser.add_argument(
        "--start-priority",
        type=int,
        default=1000,
        help="Starting priority for rules (default: 1000)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without writing files",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # When called by an Agent, it can capture this STDOUT
    args = parse_arguments()
    result = generate_nsg_tfvars(
        args.excel_path, start_priority=args.start_priority, dry_run=args.dry_run
    )
    print(result)
