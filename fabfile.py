from fabric.api import *
import datetime


def backup(dest, mysql_user, backup_name=None, databases=None, mysqldump_other_args=''):
    name = backup_name or datetime.date.today().isoformat().replace('-', '')
    dest = dest.format(name=name)
    databases = '-B' + ' '.join(databases.split(';')) if databases else '-A'

    dump_cmd = 'mysqldump -u {user} -p {databases} {other}'
    save_cmd = 'aws s3 cp - {dest}' if dest.startswith('s3://') else 'cat - > {dest}'

    run('{dump} | {save}'.format(user=mysql_user, databases=databases, dest=dest, 
                                 other=mysqldump_other_args, dump=dump_cmd,
                                 save=save_cmd))
