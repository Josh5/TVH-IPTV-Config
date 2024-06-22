# Docker Compose

Follow these instructions to configure a docker-compose.yml for your system.

> __Note__
>
> These instructions assume that you have docker and docker-compose installed for your system.
> 
> Depending on how you have installed this, the commands to execute docker compose may vary.


## PREPARE DIRECTORIES:

> __Warning__
>
> These commands are meant to be run as your user. Do not run them as root.
> 
> If you do run these commands as root, you may need to manually fix the permissions and ownership after.

Create a directory for your service:
```shell
sudo mkdir -p /opt/container-services/tvh-iptv
sudo chown -R $(id -u):$(id -g) /opt/container-services/tvh-iptv
```

If you modify the path `/opt/container-services/tvh-iptv`, ensure you also modify the path in your docker-compose.yml file below.


Create a Docker Compose file `/opt/container-services/tvh-iptv/docker-compose.yml`.

Populate this file with the contents of one of these Docker Compose templates:
- [AIO Stack with TIC & TVH in a single container (Recommended)](./compose-files/docker-compose.aio.yml).
- [Side-cart Stack with TIC & TVH in separate containers (Requires that you do some initial setup for TVH)](./compose-files/docker-compose.side-tvh.yml).

### AMD/Intel:
- [AMD and Intel GPUs](./compose-files/docker-compose.amd+intel.yml).
- [Privileged AMD and Intel GPUs Docker Compose Template](./compose-files/docker-compose.amd+intel.privileged.yml) (grants full access to host devices).

## EXECUTE:

Navigate to your compose location and execute it.
```shell
cd /opt/container-services/tvh-iptv
sudo docker-compose up -d --force-recreate --pull
```

After container executes successfully, navigate to your docker host URL in your browser on port 9985 and click connect.
`http://<host-ip>:9985/`
