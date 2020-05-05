import os
import sys
from docker.types import (RestartPolicy, Placement)

# Configuration file for jupyterhub.

## The ip for this process
c.JupyterHub.hub_ip = '0.0.0.0'

## The public facing ip of the whole application (the proxy)
c.JupyterHub.ip = '0.0.0.0'

## The class to use for spawning single-user servers.
#
#  Should be a subclass of Spawner.
c.JupyterHub.spawner_class = 'coursewareuserspawner.CoursewareUserSpawner'
c.DockerSpawner.container_ip = "0.0.0.0"
c.DockerSpawner.container_image = os.environ['CONTAINER_IMAGE']
c.DockerSpawner.network_name = os.environ['BACKEND_NETWORK']

c.JupyterHub.authenticator_class = "jhub_remote_user_authenticator.remote_user_auth.RemoteUserLocalAuthenticator"
c.LocalAuthenticator.create_system_users = True
c.LocalAuthenticator.add_user_cmd = ["/get_user_id.sh"]

c.JupyterHub.logo_file = '/var/jupyterhub/logo.png'

c.JupyterHub.admin_access = True if os.environ.get('ADMIN_ACCESS', '1') in ('yes', '1') else False

if 'CONCURRENT_SPAWN_LIMIT' in os.environ:
    c.JupyterHub.concurrent_spawn_limit = int(os.environ['CONCURRENT_SPAWN_LIMIT'])
if 'SPAWNER_HTTP_TIMEOUT' in os.environ:
    c.Spawner.http_timeout = int(os.environ['SPAWNER_HTTP_TIMEOUT'])
if 'SPAWNER_START_TIMEOUT' in os.environ:
    c.Spawner.start_timeout = int(os.environ['SPAWNER_START_TIMEOUT'])

if 'CPU_LIMIT' in os.environ:
    c.Spawner.cpu_limit = float(os.environ['CPU_LIMIT'])
if 'CPU_GUARANTEE' in os.environ:
    c.Spawner.cpu_guarantee = float(os.environ['CPU_GUARANTEE'])
if 'MEM_LIMIT' in os.environ:
    c.Spawner.mem_limit = os.environ['MEM_LIMIT']
if 'MEM_GUARANTEE' in os.environ:
    c.Spawner.mem_guarantee = os.environ['MEM_GUARANTEE']

restart_max_attempts = int(os.environ.get('SPAWNER_RESTART_MAX_ATTEMPTS', '10'))
extra_task_spec = {
    'restart_policy': RestartPolicy(
        condition='any',
        delay=5000000000,
        max_attempts=restart_max_attempts
    )
}
if 'SPAWNER_CONSTRAINTS' in os.environ:
    placement_constraints = os.environ['SPAWNER_CONSTRAINTS']
    extra_task_spec.update({
        'placement': Placement(
            constraints=[x.strip() for x in placement_constraints.split(';')]
        )
    })
c.SwarmSpawner.extra_task_spec = extra_task_spec

# DB
pg_user = os.environ['POSTGRES_ENV_JPY_PSQL_USER']
pg_pass = os.environ['POSTGRES_ENV_JPY_PSQL_PASSWORD']
pg_host = os.environ['POSTGRES_PORT_5432_TCP_ADDR']
c.JupyterHub.db_url = 'postgresql://{}:{}@{}:5432/jupyterhub'.format(
    pg_user,
    pg_pass,
    pg_host,
)

# services
services = []

## cull servers
cull_server = os.environ.get('CULL_SERVER', 'no')
if cull_server == '1' or cull_server == 'yes':
    cull_server_idle_timeout = int(os.environ.get('CULL_SERVER_IDLE_TIMEOUT', '600'))
    cull_server_max_age = int(os.environ.get('CULL_SERVER_MAX_AGE', '0'))
    cull_server_every = int(os.environ.get('CULL_SERVER_EVERY', '0'))
    if cull_server_idle_timeout > 0:
        services.append(
            {
                'name': 'cull-idle',
                'admin': True,
                'command': [sys.executable,
                            '/usr/local/bin/cull_idle_servers.py',
                            '--timeout={}'.format(str(cull_server_idle_timeout)),
                            '--max-age={}'.format(str(cull_server_max_age)),
                            '--cull-every={}'.format(str(cull_server_every))],
            }
        )
c.JupyterHub.services = services
