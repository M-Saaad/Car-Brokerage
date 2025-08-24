# Change user
# su ec2-user

# Change directory to project
cd /home/ec2-user/backend/Car-Brokerage

# Remove old certs
rm -r certs/privkey.pem certs/fullchain.pem
 
# Move fullchain
sudo cp /etc/letsencrypt/live/autobrokerai.com/fullchain.pem /home/ec2-user/backend/Car-Brokerage/certs
sudo chown -R ec2-user:ec2-user /home/ec2-user/backend/Car-Brokerage/certs/fullchain.pem

# Move private key
sudo cp /etc/letsencrypt/live/autobrokerai.com/privkey.pem /home/ec2-user/backend/Car-Brokerage/certs
sudo chown -R ec2-user:ec2-user /home/ec2-user/backend/Car-Brokerage/certs/privkey.pem

# Stop pm2 job for API
pm2 stop 1

# Start pm2 job for API
pm2 start 1