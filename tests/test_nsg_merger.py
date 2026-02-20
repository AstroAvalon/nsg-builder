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
    def test_parse_project_tfvars(self):
        content = """
        project = {
          customer          = "Contoso"
          location          = "EastUS"
          client_code       = "App1"
          environment_level = "Prd"
          address_space     = ["10.0.0.0/16"]
        }
        """
        with patch("builtins.open", mock_open(read_data=content)):
            with patch("os.path.exists", return_value=True):
                vars = azure_helper.parse_project_tfvars("dummy.tfvars")
                self.assertEqual(vars["customer"], "Contoso")
                self.assertEqual(vars["location"], "EastUS")
                self.assertEqual(vars["address_space"], ["10.0.0.0/16"])

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
      newbits = 4
      netnum = 2
    }
  }
}
"""
        with patch("builtins.open", mock_open(read_data=content)):
            with patch("os.path.exists", return_value=True):
                subnets = azure_helper.parse_subnet_config("dummy.tf")
                self.assertEqual(subnets["AppDB"]["name"], "subnet-db")
                self.assertTrue(subnets["AppDB"]["has_nsg"])
                self.assertEqual(subnets["AppDB"]["newbits"], 4)
                self.assertEqual(subnets["AppDB"]["netnum"], 2)

    def test_calculate_subnet_cidr(self):
        # 10.0.0.0/16, newbits=8 -> /24. netnum=1 -> 10.0.1.0/24
        cidr = azure_helper.calculate_subnet_cidr("10.0.0.0/16", 8, 1)
        self.assertEqual(cidr, "10.0.1.0/24")


class TestNSGMerger(unittest.TestCase):

    def setUp(self):
        mock_pd.isna.side_effect = lambda x: x is None

    @patch("nsg_merger.find_existing_file")
    @patch("azure_helper.fetch_azure_nsg_rules")
    def test_merge_nsg_rules_drift_detection(self, mock_fetch, mock_find_file):
        # 1. Setup Mock Excel DataFrame
        mock_df = MagicMock()
        mock_pd.read_excel.return_value = mock_df

        # Mock Data Structure
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

        # Filtered Result Mock
        mock_filtered_df = MagicMock()
        mock_filtered_df.iterrows.return_value = [(0, mock_row_series)]

        # Column Mock
        mock_col_series = MagicMock()
        mock_col_series.dropna.return_value.unique.return_value = ["AppSubnet"]

        # Intelligent __getitem__ side effect
        def getitem_side_effect(arg):
            if arg == "Azure Subnet Name":
                return mock_col_series
            # Fallback for boolean indexing (filtering)
            return mock_filtered_df

        mock_df.__getitem__.side_effect = getitem_side_effect

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
            "location": "eastus",
            "address_space": ["10.0.0.0/16"]
        }

        with patch("azure_helper.parse_project_tfvars", return_value=project_vars), \
             patch("azure_helper.parse_subnet_config", return_value={"AppSubnet": {"name": "AppSubnet", "has_nsg": True}}), \
             patch("os.path.exists", return_value=True), \
             patch("glob.glob", return_value=["tfvars/nsg_appsubnet.auto.tfvars"]), \
             patch("builtins.open", mock_open(read_data=existing_content)) as mock_file:

            # CALL WITH NONE for base_rules
            nsg_merger.merge_nsg_rules("test.xlsx", None, ".")

            # VERIFY WRITES
            full_output = ""
            for call in mock_file().write.call_args_list:
                full_output += str(call.args[0])

            self.assertIn('name                       = "drift1"', full_output)
            self.assertIn('priority                   = 1050', full_output)
            self.assertIn('name                       = "existing_rule"', full_output)

    @patch("nsg_merger.find_existing_file")
    def test_gateway_subnet_exclusion(self, mock_find_file):
        mock_df = MagicMock()
        mock_pd.read_excel.return_value = mock_df

        # Mock Unique returning GatewaySubnet
        mock_df.__getitem__.return_value.dropna.return_value.unique.return_value = ["GatewaySubnet"]

        with patch("builtins.print") as mock_print:
            nsg_merger.merge_nsg_rules("test.xlsx", None, ".")
            mock_find_file.assert_not_called()

    @patch("nsg_merger.find_existing_file")
    def test_merge_with_base_rules(self, mock_find_file):
        # 1. Setup Mock Pandas for TWO calls (Client Excel + Base Excel)
        mock_client_df = MagicMock()
        mock_base_df = MagicMock()
        mock_pd.read_excel.side_effect = [mock_client_df, mock_base_df]

        # 2. Setup Client DF
        client_row = {
            "Azure Subnet Name": "AppSubnet",
            "Priority": "1000",
            "Direction": "Inbound",
            "Access": "Allow",
            "Source": "1.2.3.4",
            "Destination": "*",
            "Protocol": "Tcp",
            "Destination Port": "80",
            "Description": "Client Rule",
        }
        mock_client_row = MagicMock()
        mock_client_row.__getitem__ = lambda self, k: client_row[k]

        # Mocks for Client DF
        mock_client_col = MagicMock()
        mock_client_col.dropna.return_value.unique.return_value = ["AppSubnet"]
        mock_client_df.__getitem__.side_effect = lambda arg: mock_client_col if arg == "Azure Subnet Name" else mock_client_df
        mock_client_df.iterrows.return_value = [(0, mock_client_row)]

        # 3. Setup Base DF
        base_row = {
            "Azure Subnet Name": "ALL",
            "Priority": "4000",
            "Direction": "Inbound",
            "Access": "Allow",
            "Source": "10.10.10.10",
            "Destination": "{{CurrentSubnet}}",
            "Protocol": "Tcp",
            "Destination Port": "443",
            "Description": "Base Rule",
        }
        mock_base_row = MagicMock()
        mock_base_row.__getitem__ = lambda self, k: base_row[k]
        mock_base_df.iterrows.return_value = [(0, mock_base_row)]

        # 4. Setup Config & Helpers
        project_vars = {"address_space": ["10.0.0.0/16"]}
        subnet_config = {"AppSubnet": {"name": "AppSubnet", "has_nsg": True, "newbits": 8, "netnum": 1}}

        with patch("azure_helper.parse_project_tfvars", return_value=project_vars), \
             patch("azure_helper.parse_subnet_config", return_value=subnet_config), \
             patch("azure_helper.calculate_subnet_cidr", return_value="10.0.1.0/24"), \
             patch("os.path.exists", return_value=True), \
             patch("glob.glob", return_value=[]), \
             patch("builtins.open", mock_open()) as mock_file:

            mock_find_file.return_value = None

            nsg_merger.merge_nsg_rules("client.xlsx", "base.xlsx", ".")

            # VERIFY
            full_output = ""
            for call in mock_file().write.call_args_list:
                full_output += str(call.args[0])

            self.assertIn('name                       = "AppSubnet_IN_Allow1000"', full_output)
            self.assertIn('name                       = "AppSubnet_IN_Allow4000"', full_output)
            self.assertIn('destination_address_prefix = "10.0.1.0/24"', full_output)
            self.assertNotIn('{{CurrentSubnet}}', full_output)

    @patch("nsg_merger.find_existing_file")
    def test_merge_only_base_rules(self, mock_find_file):
        # 1. Setup Mock Pandas for Base Rules (Client is None)
        mock_base_df = MagicMock()
        mock_pd.read_excel.return_value = mock_base_df

        # 2. Setup Base DF
        base_row = {
            "Azure Subnet Name": "ALL",
            "Priority": "4000",
            "Direction": "Inbound",
            "Access": "Allow",
            "Source": "10.0.0.0/8",
            "Destination": "{{CurrentSubnet}}",
            "Protocol": "Tcp",
            "Destination Port": "443",
            "Description": "Base Rule",
        }
        mock_base_row = MagicMock()
        mock_base_row.__getitem__ = lambda self, k: base_row[k]

        mock_base_df.columns.str.strip.return_value = ["Azure Subnet Name", "Priority", "Direction", "Access", "Source", "Destination", "Protocol", "Destination Port", "Description"]
        mock_base_df.iterrows.return_value = [(0, mock_base_row)]
        mock_base_df.__len__.return_value = 1

        # 3. Configure mock_pd.DataFrame to mimic empty client DF behavior
        mock_empty_df = MagicMock()
        mock_series = MagicMock()
        mock_series.dropna.return_value = mock_series
        mock_series.unique.return_value = []

        mock_empty_df.__getitem__.return_value = mock_series
        mock_empty_df.iterrows.return_value = []

        def getitem_side_effect(arg):
             if isinstance(arg, str): return mock_series # Column access
             return mock_empty_df # Filtering result
        mock_empty_df.__getitem__.side_effect = getitem_side_effect

        mock_pd.DataFrame.return_value = mock_empty_df

        # 4. Setup Config
        subnet_config = {"AppSubnet": {"name": "AppSubnet", "has_nsg": True, "newbits": 8, "netnum": 1}}
        project_vars = {"address_space": ["10.0.0.0/16"]}

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

        with patch("azure_helper.parse_project_tfvars", return_value=project_vars), \
             patch("azure_helper.parse_subnet_config", return_value=subnet_config), \
             patch("azure_helper.calculate_subnet_cidr", return_value="10.0.1.0/24"), \
             patch("os.path.exists", return_value=True), \
             patch("glob.glob", return_value=["tfvars/nsg_appsubnet.auto.tfvars"]), \
             patch("builtins.open", mock_open(read_data=existing_content)) as mock_file:

            mock_find_file.return_value = "tfvars/nsg_appsubnet.auto.tfvars"

            # RUN with None client file
            nsg_merger.merge_nsg_rules(None, "base.xlsx", ".")

            # VERIFY
            written_content = ""
            for call in mock_file().write.call_args_list:
                written_content += str(call.args[0])

            self.assertIn("AppSubnet_IN_Allow4000", written_content)
            self.assertIn('name                       = "existing_rule"', written_content)


if __name__ == "__main__":
    unittest.main()
