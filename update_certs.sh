# Change directory to project
cd /home/autobrokerai/Car-Brokerage

# Remove old certs
rm -rf certs/privkey.pem certs/fullchain.pem
 
# Extract private key
sudo awk '/BEGIN RSA PRIVATE KEY/,/END RSA PRIVATE KEY/' /var/cpanel/ssl/apache_tls/autobrokerai.com/combined > certs/privkey.pem

# Extract the first certificate (your server cert)
sudo awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/' /var/cpanel/ssl/apache_tls/autobrokerai.com/combined | head -n 100 > certs/fullchain.pem

# Stop pm2 job for API
pm2 stop 0

# Start pm2 job for API
pm2 start 0