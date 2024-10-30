source /home/autobrokerai/Car-Brokerage/.venv/bin/activate
exec uvicorn chatgpt_api:app --host 0.0.0.0 --port 8000 --ssl-keyfile /var/cpanel/ssl/apache_tls/autobrokerai.com/privkey.pem --ssl-certfile /var/cpanel/ssl/apache_tls/autobrokerai.com/fullchain.pem
