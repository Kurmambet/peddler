# 1. Сначала DNS и SSL (пока старый compose ещё работает)

docker compose -f docker-compose.prod.yml stop nginx
certbot certonly --standalone -d matrix.hushme.fun -d element.hushme.fun
docker compose -f docker-compose.prod.yml start nginx

# 2. Создать папку matrix/synapse на сервере (если ещё не)

mkdir -p /root/peddler/matrix/synapse /root/peddler/matrix/element

# 3. Положить element config.json (вручную или через git push позже)

# 4. Сгенерировать homeserver.yaml

cd /root/peddler
docker run -it --rm \
 -v $(pwd)/matrix/synapse:/data \
 -e SYNAPSE_SERVER_NAME=matrix.hushme.fun \
 -e SYNAPSE_REPORT_STATS=no \
 matrixdotorg/synapse:latest generate

# 5. Создать БД для synapse

docker exec -it peddler-db-prod psql -U ${DB_USER} \
 -c "CREATE USER synapse_user WITH PASSWORD 'StrongPass';"
docker exec -it peddler-db-prod psql -U ${DB_USER} \
 -c "CREATE DATABASE synapse ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' template=template0 OWNER synapse_user;"

# 6. Отредактировать homeserver.yaml (секция database)

nano /root/peddler/matrix/synapse/homeserver.yaml

# Теперь можно коммитить и пушить — CI отработает чисто

server_name: "matrix.hushme.fun"
pid_file: /data/homeserver.pid
listeners:

- port: 8008
  resources: - compress: false
  names: - client - federation
  tls: false
  type: http
  x\*forwarded: true
  database:
  name: psycopg2
  txn_limit: 10000
  args:
  user: synapse_user
  password: ""
  database: synapse
  host: db
  port: 5432
  cp_min: 5
  cp_max: 10
  log_config: "/data/matrix.hushme.fun.log.config"
  media_store_path: /data/media_store
  registration_shared_secret: ""
  report_stats: false
  macaroon_secret_key: ""
  form_secret: ""
  signing_key_path: "/data/matrix.hushme.fun.signing.key"
  trusted_key_servers:
- server_name: "matrix.org"

# vim:ft=yaml
