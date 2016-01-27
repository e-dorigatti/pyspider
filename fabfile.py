from fabric.api import *
import datetime


def backup(dest, mysql_user, backup_name=None, databases=None, mysqldump_other_args=''):
    name = backup_name or datetime.date.today().isoformat().replace('-', '')
    dest = dest.format(name=name)
    databases = '-B' + ' '.join(databases.split(';')) if databases else '-A'

    dump_cmd = 'mysqldump -u {user} -p {databases} {other}'
    save_cmd = 'aws s3 cp - {dest}' if dest.startswith('s3://') else 'cat - > {dest}'

    run('{dump} | {save}'.format(dump=dump_cmd, save=save_cmd).format(
        user=mysql_user, databases=databases, dest=dest, other=mysqldump_other_args)
    )


def optimize(mysql_user, database, tables=None):
    def mysqlrun(query):
        query = query.format(user=mysql_user, database=database)
        return run('mysql -u {user} -p {database} -e "{query}"'.format(
            user=mysql_user, database=database, query=query.replace('\n', '\\n')
        ))

    if tables:
        tables = tables.split(';')
    else:
        out = mysqlrun('''SELECT table_name
                          FROM information_schema.tables
                          WHERE table_schema='{database}' ''')
        tables = [row[1:-2].strip() for row in out.split('\n') if row.startswith('| ')][1:]

    mysqlrun('OPTIMIZE TABLE ' + ', '.join(tables))

