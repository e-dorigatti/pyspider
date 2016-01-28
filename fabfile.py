from fabric.api import run, put, cd, sudo
from fabric.context_managers import shell_env
from StringIO import StringIO
import random


def run_detached(command):
    tempfile = '/tmp/{}.sh'.format(
        ''.join(random.choice('0123456789abcdef') for _ in xrange(12))
    )
    put(StringIO(command), tempfile)
    run('cat ' + tempfile)
    run('screen -L -d -m bash {}; sleep 0'.format(tempfile))
    run('rm ' + tempfile)


def backup(pguser, pgpassword, pghost='localhost', pgport='5432', compress=True,
           out_file='/tmp/out.postgre.sql.gz', pgdump_additional_parameters='-c',
           detach=False):

    compress = compress in {True, 'Y', 'y', 'yes', 'true'}
    detach = detach in {True, 'Y', 'y', 'yes', 'true'}

    epilogue = pgdump_additional_parameters
    if compress:
        epilogue += ' | gzip '

    if out_file.startswith('s3://'):
        epilogue += '| aws s3 cp - ' + out_file
    else:
        epilogue += ' > ' + out_file

    with shell_env(PGUSER=pguser, PGPASSWORD=pgpassword,
                   PGHOST=pghost, PGPORT=pgport):
        command = 'pg_dumpall ' + epilogue
        if detach:
            run_detached(command)
        else:
            run(command)


def deploy(pyspider_base_dir, docker_base_dir):
    with cd(pyspider_base_dir):
        sudo('git pull')
        sudo('docker build -t user/pyspider .')

    with cd(docker_base_dir):
        sudo('docker-compose up -d')