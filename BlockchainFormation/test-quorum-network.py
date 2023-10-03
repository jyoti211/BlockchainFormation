import paramiko
import os
from BlockchainFormation.utils.utils import *
from BlockchainFormation.Node_Handler import *
from scp import SCPClient

from DAppFormation.blockchain_specifics.quorum.Quorum_DApp import Quorum_DApp

# List of client configurations
clients = [
    {
        'hostname': '18.134.139.236',
        'port': 22,
        'username': 'ubuntu',
    }
]
ssh_clients = []
scp_clients = []
priv_ips = ['18.134.139.236'],#public ip
client_config = {
    "priv_ips": ['18.134.139.236'],
}
     
def configure_quorum():
        
    try:
        with open("/var/www/html/DLPS/BlockchainFormation/BlockchainFormation/experiments/exp_2023-08-28_10-34-19_quorum/config.json") as json_file:
            quorum_config = json.load(json_file)
    
        node_handler = Node_Handler(quorum_config)
        node_handler.create_ssh_scp_clients()
        Quorum_Network.startup(node_handler)
        #ssh_clients = node_handler.ssh_clients
        #Quorum_Network.getAdminPeers(quorum_config, ssh_clients, logger)
        #Quorum_Network.initiate_transaction_web3(quorum_config, ssh_clients, logger)
   

    except Exception as e:
            print(f"An error occurred : {str(e)}")
        


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    configure_quorum()