#!/bin/bash

# Run a Pulp in one container, and reset the admin password to 'password'.
# Use only for testing!

set -eu
set -o pipefail

mkdir -p settings

PULP_TAG=${PULP_TAG:3.18}

cat << EOF > settings/settings.py
CONTENT_ORIGIN='http://$(hostname):8080'
ANSIBLE_API_HOSTNAME='http://$(hostname):8080'
ANSIBLE_CONTENT_HOSTNAME='http://$(hostname):8080/pulp/content'
TOKEN_AUTH_DISABLED=True
EOF

# Run Pulp in one container.
docker run \
  --detach \
  --name pulp \
  --volume "$(pwd)/settings":/etc/pulp \
  --publish 8080:80 \
  pulp/pulp:$PULP_TAG

# Wait for it to come up.
attempts=0
until curl --fail http://localhost:8080/pulp/api/v3/status/ > /dev/null 2>&1; do
  sleep 2
  attempts=$((attempts + 1))
  if [[ $attempts -ge 60 ]]; then
    echo "Timed out waiting for pulp"
    docker logs pulp
    exit 1
  fi
done

# Reset the admin password.
docker exec pulp pulpcore-manager reset-admin-password --password password
