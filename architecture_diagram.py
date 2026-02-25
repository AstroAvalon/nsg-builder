# architecture_diagram.py
#
# This script generates an architectural diagram of the Terraform deployment using the 'diagrams' Python library.
#
# Prerequisites:
# 1. Install Graphviz: https://graphviz.org/download/
# 2. Install the diagrams library: pip install diagrams
#
# Usage:
# python architecture_diagram.py
#
# This will generate a file named 'azure_architecture.png'.

from diagrams import Diagram, Cluster, Edge
from diagrams.azure.network import VirtualNetworks, Subnets, Nat, NetworkSecurityGroups, PrivateEndpoint
from diagrams.azure.integration import LogicApps
from diagrams.azure.compute import Automation
from diagrams.azure.storage import StorageAccounts
from diagrams.azure.engagement import CommunicationServices
from diagrams.azure.general import User

# Define generic names for clarity
VNET_NAME = "Virtual Network"
GATEWAY_SUBNET_NAME = "Gateway Subnet"
PRIVATE_LINK_SUBNET_NAME = "Private Link Subnet"
DATABASE_SUBNET_NAME = "Database Subnet"
BUDGET_BOOKS_SUBNET_NAME = "App Subnet (Budget)"
TEST_SAVVY_SUBNET_NAME = "App Subnet (Test)"
MGMT_TOOLS_SUBNET_NAME = "Management Subnet"
REPORTING_SUBNET_NAME = "Reporting Subnet"

with Diagram("Azure Architecture", show=False, direction="TB", filename="azure_architecture"):

    # User / Trigger
    user = User("User / Event")

    with Cluster("Azure Subscription"):

        # Communication Services (Global / Regional Resource, separate from VNet)
        acs = CommunicationServices("Communication Services")

        with Cluster(VNET_NAME):

            # NAT Gateway (Associated with multiple subnets)
            nat_gw = Nat("NAT Gateway")

            # Subnets Definitions
            with Cluster(GATEWAY_SUBNET_NAME):
                gateway_subnet = Subnets(GATEWAY_SUBNET_NAME)
                # No NSG on GatewaySubnet

            with Cluster(PRIVATE_LINK_SUBNET_NAME):
                pl_subnet = Subnets(PRIVATE_LINK_SUBNET_NAME)
                pl_nsg = NetworkSecurityGroups("NSG")

                # Private Endpoints reside here
                logic_app_pe = PrivateEndpoint("Logic App PE")
                automation_pe = PrivateEndpoint("Automation PE")

                pl_subnet - pl_nsg

            with Cluster(DATABASE_SUBNET_NAME):
                db_subnet = Subnets(DATABASE_SUBNET_NAME)
                db_nsg = NetworkSecurityGroups("NSG")
                db_subnet - db_nsg

            with Cluster(BUDGET_BOOKS_SUBNET_NAME):
                bb_subnet = Subnets(BUDGET_BOOKS_SUBNET_NAME)
                bb_nsg = NetworkSecurityGroups("NSG")
                bb_subnet - bb_nsg

            with Cluster(TEST_SAVVY_SUBNET_NAME):
                ts_subnet = Subnets(TEST_SAVVY_SUBNET_NAME)
                ts_nsg = NetworkSecurityGroups("NSG")
                ts_subnet - ts_nsg

            with Cluster(MGMT_TOOLS_SUBNET_NAME):
                mt_subnet = Subnets(MGMT_TOOLS_SUBNET_NAME)
                mt_nsg = NetworkSecurityGroups("NSG")
                mt_subnet - mt_nsg

            with Cluster(REPORTING_SUBNET_NAME):
                rpt_subnet = Subnets(REPORTING_SUBNET_NAME)
                rpt_nsg = NetworkSecurityGroups("NSG")

                # Logic App VNet Integration Endpoint
                logic_app_vnet_int = Subnets("VNet Integration")

                rpt_subnet - rpt_nsg

            # NAT Gateway Connections
            # Connected to all except GatewaySubnet
            nat_gw >> [pl_subnet, db_subnet, bb_subnet, ts_subnet, mt_subnet, rpt_subnet]

        # PaaS Resources (Outside VNet, connected via PE/VNet Int)

        with Cluster("Reporting Services"):
            logic_app = LogicApps("Logic App\n(Standard)")
            automation = Automation("Automation Account")
            storage = StorageAccounts("Storage Account\n(Reports)")

            # Logic App Connections
            # 1. VNet Integration (Outbound)
            logic_app >> Edge(label="VNet Integration") >> rpt_subnet

            # 2. Private Endpoint (Inbound)
            logic_app_pe >> Edge(style="dotted", label="Private Link") >> logic_app

            # 3. Storage Access
            logic_app >> Edge(label="Uses") >> storage

            # Automation Account Connections
            # 1. Private Endpoint (Inbound/Outbound via Hybrid Worker if applicable, usually Inbound for Webhooks)
            automation_pe >> Edge(style="dotted", label="Private Link") >> automation

            # 2. Storage Access (Managed Identity)
            automation >> Edge(label="Blob Data Contributor") >> storage

    # External Interactions
    user >> acs
    user >> logic_app
