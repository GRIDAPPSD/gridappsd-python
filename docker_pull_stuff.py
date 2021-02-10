import docker
from gridappsd.docker_handler import run_dependency_containers

# with run_dependency_containers(stop_after=False) as f:
#     pass

client = docker.from_env()

client.images.pull("gridappsd/gridappsd:develop")

args = {
    'gridappsd':
        {
            'environment':
                {
                    'DEBUG': 1,
                    'PATH': '/gridappsd/bin:/gridappsd/lib:/gridappsd/services/fncsgossbridge/service:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin',
                    'START': 1},
            'image': 'gridappsd/gridappsd:develop',
            'links': {'blazegraph': 'blazegraph',
                      'influxdb': 'influxdb',
                      'mysql': 'mysql',
                      'proven': 'proven',
                      'redis': 'redis'},
            'ports': {'61613/tcp': 61613,
                      '61614/tcp': 61614,
                      '61616/tcp': 61616},
            'pull': True,
            'start': True,
            'volumes': {
                '/home/gridappsd/repos/gridappsd-python/gridappsd/conf/entrypoint.sh': {
                    'bind': '/gridappsd/entrypoint.sh',
                    'mode': 'rw'},
                '/home/gridappsd/repos/gridappsd-python/gridappsd/conf/run-gridappsd.sh': {
                    'bind': '/gridappsd/run-gridappsd.sh',
                    'mode': 'rw'}
            }
        }
}

client.containers.run(**args['gridappsd'])
