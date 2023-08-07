#!/bin/bash
echo "move to /home/ubuntu"
cd /home/ubuntu
sudo chown -R ubuntu /home/ubuntu
pwd
whoami
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
sudo mv /.nvm /home/ubuntu/
export NVM_DIR="/home/ubuntu/.nvm"
echo $NVM_DIR
chown -R ubuntu:ubuntu /home/ubuntu/.nvm
chmod +x /home/ubuntu/.nvm/nvm.sh
chmod +x /home/ubuntu/.bashrc
chmod +x /home/ubuntu/.profile


sudo -E -u ubuntu bash -c "source /home/ubuntu/.nvm/nvm.sh && nvm -v"
sudo -E -u ubuntu bash -c "source /home/ubuntu/.nvm/nvm.sh && nvm install 14 && nvm use 14"
sudo ln -s /home/ubuntu/.nvm/versions/node/v14.21.3/bin/node /usr/bin/node
sudo ln -s /home/ubuntu/.nvm/versions/node/v14.21.3/bin/npm /usr/bin/npm

npm -v
node -v
npm install -g truffle
#. /home/ubuntu/.profile
#truffle version 


sudo touch /var/log/user_data_success.log 
sudo echo "SUCCESSFULL"
