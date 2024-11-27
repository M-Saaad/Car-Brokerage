source /home/autobrokerai/Car-Brokerage/.venv/bin/activate
exec uvicorn chatgpt_api:app --host 0.0.0.0 --port 8000 --ssl-keyfile certs/privkey.pem --ssl-certfile certs/fullchain.pem
