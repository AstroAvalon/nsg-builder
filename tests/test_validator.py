import sys
import os
import unittest
from unittest.mock import MagicMock, patch, mock_open

# --- MOCK DEPENDENCIES BEFORE IMPORTING ---
mock_pd = MagicMock()
sys.modules["pandas"] = mock_pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import validator
import azure_helper

class TestValidator(unittest.TestCase):

    def setUp(self):
        # Configure mock_pd.isna to work like pd.isna
        mock_pd.isna.side_effect = lambda x: x is None

    def _setup_mock_df(self, row_data_list):
        mock_df = MagicMock()
        mock_pd.read_excel.return_value = mock_df

        # Columns strip
        mock_df.columns.str.strip.return_value = mock_df.columns

        # Filtering: df[df["Col"] != "Val"] returns df (simplified)
        # We can just return self for filtering to keep it simple, assuming no GatewaySubnet in test data
        mock_df.__getitem__.return_value = mock_df

        # to_dict returns the data
        mock_df.to_dict.return_value = row_data_list

        return mock_df

    @patch("validator.find_existing_file")
    @patch("builtins.open", new_callable=mock_open)
    @patch("sys.exit")
    def test_validate_simple_match(self, mock_exit, mock_file, mock_find_file):
        # 1. Setup Data
        row_data = {
            "Azure Subnet Name": "AppSubnet",
            "Direction": "Inbound",
            "Access": "Allow",
            "Protocol": "Tcp",
            "Source": "1.2.3.4",
            "Destination": "*",
            "Destination Port": "80",
            "Description": "Test Rule",
        }
        self._setup_mock_df([row_data])

        # 2. Setup TFVars Content
        tfvars_content = """
        nsg_rules = [
          {
            name = "rule1"
            priority = 100
            direction = "Inbound"
            access = "Allow"
            protocol = "Tcp"
            source_address_prefix = "1.2.3.4"
            destination_address_prefix = "*"
            destination_port_range = "80"
          }
        ]
        """
        mock_file.return_value.read.return_value = tfvars_content

        # 3. Mocks
        project_vars = {"address_space": ["10.0.0.0/16"]}
        subnet_config = {"AppSubnet": {"name": "AppSubnet", "has_nsg": True}}

        with patch("azure_helper.parse_project_tfvars", return_value=project_vars), \
             patch("azure_helper.parse_subnet_config", return_value=subnet_config):

            mock_find_file.return_value = "tfvars/nsg.auto.tfvars"

            # Run
            validator.validate("test.xlsx", None, ".")

            # Verify
            mock_exit.assert_called_with(0)

    @patch("validator.find_existing_file")
    @patch("builtins.open", new_callable=mock_open)
    @patch("sys.exit")
    def test_validate_missing_rule(self, mock_exit, mock_file, mock_find_file):
        # 1. Setup Data
        row_data = {
            "Azure Subnet Name": "AppSubnet",
            "Direction": "Inbound",
            "Access": "Allow",
            "Protocol": "Tcp",
            "Source": "1.2.3.4",
            "Destination": "*",
            "Destination Port": "80",
            "Description": "Test Rule",
        }
        self._setup_mock_df([row_data])

        # 2. Setup TFVars Content (Mismatch Port)
        tfvars_content = """
        nsg_rules = [
          {
            direction = "Inbound"
            access = "Allow"
            protocol = "Tcp"
            source_address_prefix = "1.2.3.4"
            destination_address_prefix = "*"
            destination_port_range = "443"  # Mismatch!
          }
        ]
        """
        mock_file.return_value.read.return_value = tfvars_content

        with patch("azure_helper.parse_project_tfvars", return_value={}), \
             patch("azure_helper.parse_subnet_config", return_value={"AppSubnet": {}}):

            mock_find_file.return_value = "tfvars/nsg.auto.tfvars"

            validator.validate("test.xlsx", None, ".")

            # Verify Failure
            mock_exit.assert_called_with(1)

if __name__ == "__main__":
    unittest.main()
