#  Copyright 2019  ChainLab
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.



import os
import time
import numpy as np
from BlockchainFormation.utils.utils import *

import hashlib


def corda_shutdown(config, logger, ssh_clients, scp_clients):
    """
    runs the corda specific shutdown operations (e.g. pulling the associated logs from the VMs)
    :return:
    """

    pass


def corda_startup(config, logger, ssh_clients, scp_clients):
    """
    Runs the corda specific startup script
    :return:
    """

    # Creating docker swarm
    logger.info("Preparing & starting docker swarm")

    stdin, stdout, stderr = ssh_clients[0].exec_command("sudo docker swarm init")
    out = stdout.readlines()
    # for index, _ in enumerate(out):
    #     logger.debug(out[index].replace("\n", ""))

    # logger.debug("".join(stderr.readlines()))

    stdin, stdout, stderr = ssh_clients[0].exec_command("sudo docker swarm join-token manager")
    out = stdout.readlines()
    # logger.debug(out)
    # logger.debug("".join(stderr.readlines()))
    join_command = out[2].replace("    ", "").replace("\n", "")

    for index, _ in enumerate(config['priv_ips']):

        if index != 0:
            stdin, stdout, stderr = ssh_clients[index].exec_command("sudo " + join_command)
            out = stdout.readlines()
            logger.debug(out)
            logger.debug("".join(stderr.readlines()))

    # Name of the swarm network
    my_net = "my-net"
    stdin, stdout, stderr = ssh_clients[0].exec_command(f"sudo docker network create --subnet 10.10.0.0/16 --attachable --driver overlay {my_net}")
    out = stdout.readlines()
    logger.debug(out)
    logger.debug("".join(stderr.readlines()))
    network = out[0].replace("\n", "")

    time.sleep(5)

    logger.info("Testing whether setup was successful")
    stdin, stdout, stderr = ssh_clients[0].exec_command("sudo docker node ls")
    out = stdout.readlines()
    for index, _ in enumerate(out):
        logger.debug(out[index].replace("\n", ""))

    logger.debug("".join(stderr.readlines()))
    if len(out) == len(config['priv_ips']) + 1:
        logger.info("Docker swarm started successfully")
    else:
        logger.info("Docker swarm setup was not successful")
        logger.info(f"Expected length: {len(config['priv_ips']) + 1}, actual length: {len(out)}")
        # sys.exit("Fatal error when performing docker swarm setup")


    logger.info(f"Started Corda")

    logger.info("Uploading the customized build.gradle and generating node documents")
    stdin, stdout, stderr = ssh_clients[0].exec_command("rm /data/samples/cordapp-example/workflows-kotlin/build.gradle")
    logger.debug(stdout.readlines())
    logger.debug(stderr.readlines())
    # wait_and_log(stdout, stderr)
    write_config(config, logger)

    scp_clients[0].put(f"{config['exp_dir']}/setup/build.gradle", "/data/samples/cordapp-example/workflows-kotlin/build.gradle")
    stdin, stdout, stderr = ssh_clients[0].exec_command("(cd /data/samples/cordapp-example && ./gradlew deployNodes)")
    logger.debug(stdout.readlines())
    logger.debug(stderr.readlines())
    # wait_and_log(stdout, stderr)

    logger.info("Getting the generated files and distributing them to the nodes")
    scp_clients[0].get("/data/samples/cordapp-example/workflows-kotlin/build/nodes", f"{config['exp_dir']}/setup", recursive=True)
    stdin, stdout, stderr = ssh_clients[0].exec_command("(cd /data/samples/cordapp-example/workflows-kotlin && rm -r build)")
    logger.debug(stdout.readlines())
    logger.debug(stderr.readlines())
    for node, _ in enumerate(config['priv_ips']):
        stdin, stdout, stderr = ssh_clients[node].exec_command("(cd /data/samples/cordapp-example/workflows-kotlin && mkdir build && cd build && mkdir nodes)")
        logger.debug(stdout.readlines())
        logger.debug(stderr.readlines())

        if node == 0:
            scp_clients[node].put(f"{config['exp_dir']}/setup/nodes/Notary", "/data/samples/cordapp-example/workflows-kotlin/build/nodes", recursive=True)
            scp_clients[node].put(f"{config['exp_dir']}/setup/nodes/Notary_node.conf", "/data/samples/cordapp-example/workflows-kotlin/build/nodes")
        else:
            scp_clients[node].put(f"{config['exp_dir']}/setup/nodes/Party{node}", "/data/samples/cordapp-example/workflows-kotlin/build/nodes", recursive=True)
            scp_clients[node].put(f"{config['exp_dir']}/setup/nodes/Party{node}_node.conf", "/data/samples/cordapp-example/workflows-kotlin/build/nodes")

    logger.info("Starting all nodes")
    channels = []
    for node, _ in enumerate(config['priv_ips']):
        if node != 0:
            channel = ssh_clients[node].get_transport().open_session()
            channel.exec_command(f"(cd /data/samples/cordapp-example/workflows-kotlin/build/nodes/Party{node} && java -jar corda.jar >> ~/node.log 2>&1)")
            channels.append(channel)



def corda_restart(config, logger, ssh_clients, scp_clients):
    """
    Runs the corda specific startup script
    :return:
    """

    pass

def write_config(config, logger):

    dir_name = os.path.dirname(os.path.realpath(__file__))
    logger.debug(f"Dir_name: {dir_name}")
    os.system(f"cp {dir_name}/setup/build_raw.gradle {config['exp_dir']}/setup/build.gradle")

    f = open(f"{config['exp_dir']}/setup/build.gradle", "a")
    
    f.write("task deployNodes(type: Cordform, dependsOn: ['jar']) {\n")
    f.write("    nodeDefaults {\n")
    f.write("        cordapp project(':contracts-kotlin')\n")
    f.write("    }\n")

    for node, ip in enumerate(config['priv_ips']):

        if node == 0:

            f.write("    node {\n")
            f.write(f"        name 'O=Notary,L=London,C=GB'\n")
            f.write(f"        notary = [validating : false]\n")
            f.write(f"        p2pAddress ('{ip}:10000')\n")
            f.write("        rpcSettings {\n")
            f.write(f"            address('{ip}:10001')\n")
            f.write(f"            adminAddress('localhost:10002')\n")
            f.write("        }\n")
            f.write("        projectCordapp {\n")
            f.write(f"            deploy = false\n")
            f.write("        }\n")
            f.write(f"        cordapps.clear()\n")
            f.write("    }\n")

        else:

            f.write("    node {\n")
            f.write(f"        name 'O=Party{node},L=London,C=GB'\n")
            f.write(f"        p2pAddress ('{ip}:10000')\n")
            f.write("        rpcSettings {\n")
            f.write(f"            address('{ip}:10001')\n")
            f.write(f"            adminAddress('localhost:10002')\n")
            f.write("        }\n")
            # f.write("        artemisPort 10002\n")
            # f.write("        webAddress ('0.0.0.0:10003')\n")
            # f.write("        webPort 10003")
            # f.write("        devMode = true")
            f.write(f"        rpcUsers = [[user: 'user1', 'password': 'test', 'permissions': ['ALL']]]\n")
            f.write("    }\n")

    f.write("}\n")

    f.close()

