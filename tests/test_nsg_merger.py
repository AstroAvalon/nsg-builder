import sys
import os
import unittest
from unittest.mock import MagicMock, patch, mock_open

# --- MOCK DEPENDENCIES BEFORE IMPORTING MODULES ---
# 1. Mock Pandas
mock_pd = MagicMock()
sys.modules["pandas"] = mock_pd

# 2. Mock Azure Libraries
mock_azure_identity = MagicMock()
sys.modules["azure.identity"] = mock_azure_identity
mock_azure_network = MagicMock()
sys.modules["azure.mgmt.network"] = mock_azure_network

# Now we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import azure_helper
import nsg_merger


class TestAzureHelper(unittest.TestCase):
    # (Keeping existing tests for azure_helper as they are unchanged)
    def test_parse_project_tfvars(self):
        content = """
        project = {
          customer          = "Contoso"
          location          = "EastUS"
          client_code       = "App1"
          environment_level = "Prd"
        }
        """
        with patch("builtins.open", mock_open(read_data=content)):
            with patch("os.path.exists", return_value=True):
                vars = azure_helper.parse_project_tfvars("dummy.tfvars")
                self.assertEqual(vars["customer"], "Contoso")
                self.assertEqual(vars["location"], "EastUS")

    def test_get_resource_group_name(self):
        vars = {
            "customer": "CuStOmEr",
            "client_code": "CLI",
            "location": "LOC",
            "environment_level": "ENV",
        }
        rg = azure_helper.get_resource_group_name(vars)
        self.assertEqual(rg, "rg-customer-cli-loc-env-network")

    def test_parse_subnet_config(self):
        content = """
locals {
  subnet_config = {
    AppDB = {
      name = "subnet-db"
      has_nsg = true
    }
    AppWeb = {
      name = "subnet-web"
      has_nsg = false
    }
  }
}
"""
        with patch("builtins.open", mock_open(read_data=content)):
            with patch("os.path.exists", return_value=True):
                subnets = azure_helper.parse_subnet_config("dummy.tf")
                self.assertEqual(subnets["AppDB"]["name"], "subnet-db")
                self.assertTrue(subnets["AppDB"]["has_nsg"])
                self.assertEqual(subnets["AppWeb"]["name"], "subnet-web")
                self.assertFalse(subnets["AppWeb"]["has_nsg"])

    def test_get_nsg_name(self):
        nsg = azure_helper.get_nsg_name("mysubnet", "prd")
        self.assertEqual(nsg, "NSG-PRD-mysubnet")

    def test_fetch_azure_nsg_rules(self):
        mock_client = sys.modules["azure.mgmt.network"].NetworkManagementClient
        mock_nsg_client = mock_client.return_value.network_security_groups

        rule1 = MagicMock()
        rule1.name = "rule1"
        rule1.priority = 100
        rule1.direction = "Inbound"
        rule1.access = "Allow"
        rule1.protocol = "Tcp"
        rule1.source_address_prefix = "*"
        rule1.destination_address_prefix = "*"
        rule1.destination_port_range = "80"

        rule_default = MagicMock()
        rule_default.priority = 65000

        mock_nsg_client.get.return_value.security_rules = [rule1, rule_default]

        rules = azure_helper.fetch_azure_nsg_rules("rg", "nsg", "sub_id")

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].priority, 100)
        self.assertEqual(rules[0].name, "rule1")


class TestNSGMerger(unittest.TestCase):

    def setUp(self):
        # Setup common mocks for nsg_merger
        # Essential: Fix pd.isna to behave correctly for strings
        mock_pd.isna.side_effect = lambda x: x is None

    @patch("nsg_merger.find_existing_file")
    @patch("azure_helper.fetch_azure_nsg_rules")
    def test_merge_nsg_rules_drift_detection(self, mock_fetch, mock_find_file):
        # 1. Setup Mock Excel DataFrame
        mock_df = MagicMock()
        mock_pd.read_excel.return_value = mock_df

        row_data = {
            "Azure Subnet Name": "AppSubnet",
            "Priority": "1000",
            "Direction": "Inbound",
            "Access": "Allow",
            "Source": "*",
            "Destination": "*",
            "Protocol": "Tcp",
            "Destination Port": "80",
            "Description": "Test Rule",
        }

        mock_row_series = MagicMock()
        mock_row_series.__getitem__ = lambda self, k: row_data[k]

        mock_subset_df = MagicMock()
        mock_subset_df.iterrows.return_value = [(0, mock_row_series)]
        mock_df.groupby.return_value = [("AppSubnet", mock_subset_df)]
        mock_df.columns.str.strip.return_value = mock_df.columns

        # 2. Setup Existing File Content
        existing_content = """
        AppSubnet_nsg_rules = [
          {
            name = "existing_rule"
            priority = 1000
            direction = "Inbound"
            access = "Allow"
            protocol = "Tcp"
            source_address_prefix = "*"
            destination_address_prefix = "*"
            destination_port_range = "443"
          }
        ]
        """

        mock_find_file.return_value = "tfvars/nsg_appsubnet.auto.tfvars"

        # 3. Setup Azure Drift Rule
        drift_rule = MagicMock()
        drift_rule.name = "drift1"
        drift_rule.priority = 1050
        drift_rule.direction = "Inbound"
        drift_rule.access = "Allow"
        drift_rule.protocol = "Tcp"
        drift_rule.source = "*"
        drift_rule.destination = "*"
        drift_rule.dest_port = "22"
        mock_fetch.return_value = [drift_rule]

        # 4. Mock Project Vars & Subnet Config
        project_vars = {
            "environment_level": "dev",
            "customer_subscription_id": "sub1",
            "customer": "Contoso",
            "client_code": "App",
            "location": "eastus"
        }

        with patch("azure_helper.parse_project_tfvars", return_value=project_vars), \
             patch("azure_helper.parse_subnet_config", return_value={"AppSubnet": {"name": "AppSubnet", "has_nsg": True}}), \
             patch("os.path.exists", return_value=True), \
             patch("glob.glob", return_value=["tfvars/nsg_appsubnet.auto.tfvars"]), \
             patch("builtins.open", mock_open(read_data=existing_content)) as mock_file:

            nsg_merger.merge_nsg_rules("test.xlsx", ".")

            # VERIFY
            handle = mock_file()
            # Combine all write calls
            full_output = "".join([call.args[0] for call in handle.write.call_args_list])

            # Note: mock_open reuse for both read/write can be tricky if not careful,
            # but usually write calls are appended to the mock.
            # However, if read_data is set, sometimes write() doesn't affect read_data.
            # We are checking what was PASSED to write().

            self.assertIn('name                       = "drift1"', full_output)
            self.assertIn('priority                   = 1050', full_output)
            self.assertIn('name                       = "existing_rule"', full_output)

            # Ensure proper sorting
            pos_1000 = full_output.find('priority                   = 1000')
            pos_1050 = full_output.find('priority                   = 1050')
            self.assertLess(pos_1000, pos_1050, "Rules should be sorted by priority")

    @patch("nsg_merger.find_existing_file")
    def test_gateway_subnet_exclusion(self, mock_find_file):
        mock_df = MagicMock()
        mock_pd.read_excel.return_value = mock_df

        # Mock groupby returning GatewaySubnet
        mock_df.groupby.return_value = [("GatewaySubnet", MagicMock())]
        mock_df.columns.str.strip.return_value = mock_df.columns

        with patch("builtins.print") as mock_print:
            nsg_merger.merge_nsg_rules("test.xlsx", ".")

            # Verify skipping message
            found = False
            for call in mock_print.call_args_list:
                if "Skipping Restricted Subnet" in str(call):
                    found = True
                    break
            self.assertTrue(found, "Should have printed skipping message")

if __name__ == "__main__":
    unittest.main()
