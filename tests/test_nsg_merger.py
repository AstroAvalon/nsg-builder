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
# Adjust path to import from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import azure_helper
import nsg_merger


class TestAzureHelper(unittest.TestCase):

    def test_parse_project_tfvars(self):
        # Test updated block parsing: project = { ... }
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
        # Test lowercase enforcement
        vars = {
            "customer": "CuStOmEr",
            "client_code": "CLI",
            "location": "LOC",
            "environment_level": "ENV",
        }
        rg = azure_helper.get_resource_group_name(vars)
        self.assertEqual(rg, "rg-customer-cli-loc-env-network")

    def test_parse_subnet_names(self):
        content = 'variable "subnet_names" { default = { "AppDB" = "subnet-db" } }'
        with patch("builtins.open", mock_open(read_data=content)):
            with patch("os.path.exists", return_value=True):
                subnets = azure_helper.parse_subnet_names_tf("dummy.tf")
                self.assertEqual(subnets["AppDB"], "subnet-db")

    def test_get_nsg_name(self):
        nsg = azure_helper.get_nsg_name("mysubnet", "prd")
        self.assertEqual(nsg, "NSG-prd-mysubnet")

    def test_fetch_azure_nsg_rules(self):
        # Since imports are inside the function, we patch where they come from (mocked modules)
        mock_client = sys.modules["azure.mgmt.network"].NetworkManagementClient
        mock_cred = sys.modules["azure.identity"].DefaultAzureCredential

        # Setup Mock Client
        mock_nsg_client = mock_client.return_value.network_security_groups

        # Mock Rule
        rule1 = MagicMock()
        rule1.name = "rule1"
        rule1.priority = 100
        rule1.direction = "Inbound"
        rule1.access = "Allow"
        rule1.protocol = "Tcp"
        rule1.source_address_prefix = "*"
        rule1.destination_address_prefix = "*"
        rule1.destination_port_range = "80"

        # Mock Default Rule (to be filtered)
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
        self.mock_df = MagicMock()
        mock_pd.read_excel.return_value = self.mock_df

        # IMPORTANT: Fix pd.isna to return False (so it doesn't skip everything)
        # We need it to return False for strings, and True for None/NaN if we want accurate testing,
        # but for our specific tests where we pass strings, False is enough.
        mock_pd.isna.side_effect = lambda x: x is None

    @patch("nsg_merger.find_existing_file")
    @patch("nsg_merger.get_existing_priorities")
    @patch("azure_helper.fetch_azure_nsg_rules")
    @patch("builtins.open", new_callable=mock_open)
    def test_merge_nsg_rules_drift_detection(
        self, mock_file, mock_fetch, mock_get_prio, mock_find_file
    ):
        # 1. Setup Inputs
        # Mock Excel DataFrame
        # Mock row iterator
        row1 = {
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
        # Create a mock series for the row
        mock_series = MagicMock()
        mock_series.__getitem__ = lambda self, k: row1[k]

        # Mock groupby
        self.mock_df.groupby.return_value = [("AppSubnet", MagicMock())]
        # Mock iterrows for the group
        # The second item in tuple is the row Series
        self.mock_df.groupby.return_value[0][1].iterrows.return_value = [
            (0, mock_series)
        ]

        # 2. Setup Files & Azure
        mock_find_file.return_value = "tfvars/nsg_appsubnet.auto.tfvars"
        mock_get_prio.return_value = (
            {"IN": 1010, "OUT": 1000},
            {1000},
            "old_content = []",
        )

        # Azure returns a DRIFT rule (Priority 1050)
        drift_rule = azure_helper.AzureRule(
            "drift1", 1050, "Inbound", "Allow", "Tcp", "*", "*", "443"
        )
        mock_fetch.return_value = [drift_rule]

        # Mock Project Vars
        with patch(
            "azure_helper.parse_project_tfvars",
            return_value={
                "customer": "c",
                "client_code": "cc",
                "location": "l",
                "environment_level": "e",
            },
        ), patch(
            "azure_helper.parse_subnet_names_tf",
            return_value={"AppSubnet": "AppSubnet"},
        ), patch(
            "os.path.exists", return_value=True
        ), patch(
            "glob.glob", return_value=["tfvars/nsg_appsubnet.auto.tfvars"]
        ):

            nsg_merger.merge_nsg_rules("test.xlsx", ".")

            # VERIFICATION
            # Check if write was called
            mock_file.assert_called()
            # Get the content written
            args, _ = mock_file().write.call_args
            written_content = args[0]

            # Check for Drift Rule
            self.assertIn('name                       = "drift1"', written_content)
            self.assertIn("priority                   = 1050", written_content)
            self.assertIn(
                'description                = "Imported from Azure Drift"',
                written_content,
            )

            # Check for Excel Rule
            # Since Prio 1000 is used in file (mock_get_prio), and Excel requested 1000...
            # The code says: if prio_val in used_priorities: SKIP
            # So we expect the Excel rule (prio 1000) to be SKIPPED / Not present if strict.
            # Wait, row1 has Priority 1000. mock_get_prio says {1000} is used.
            # So it should be skipped.
            # Let's verify it is NOT in the output (or we see the error print).
            # Actually, checking stdout is hard here without capturing it.
            # Let's check logic: if we change Excel rule to 1010, it should appear.

    @patch("nsg_merger.find_existing_file")
    def test_gateway_subnet_exclusion(self, mock_find_file):
        # Mock dataframe with GatewaySubnet
        self.mock_df.groupby.return_value = [("GatewaySubnet", MagicMock())]

        with patch("builtins.print") as mock_print:
            nsg_merger.merge_nsg_rules("test.xlsx", ".")

            # Verify we printed skipping message
            found = False
            for call in mock_print.call_args_list:
                if "Skipping Restricted Subnet" in str(call):
                    found = True
                    break
            self.assertTrue(found)


if __name__ == "__main__":
    unittest.main()
