#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-11-05 10:42:24

import time
import mysql.connector
from mysql.connector import pooling


class IteratorWrapper(object):
    def __init__(self, iterator, **kwargs):
        self.iterator = iterator
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def next(self):
        return self.iterator.next()


class CleaningCursor(object):
    """ Proxies everything to the real cursor, but cleans up resources when finished

    Note well: The typical usage of cursors in pyspider is

        for row in db.execute(query):
            do_something_with(row)

    What happens is:
     1. db.execute returns a cursor
     2. cursor.__iter__ returns a callable-iterator
     3. the (only) reference to the cursor is discarded
     4. the cursor is garbage-collected, so the cursor and the connection get closed
     5. the iterator is scanned, but it won't return any item as the connection is closed

    To avoid garbage collection at step 4 it is neccessary to hold a reference to the
    cursor, this is exactly the reason why IteratorWrapper exists. In this way, the
    cursor will be reachable as long as the iterator is reachable.
    """
    def __init__(self, cursor, connection):
        self.connection = connection
        self.cursor = cursor

    def __getattr__(self, attr):
        return getattr(self.cursor, attr)

    def __iter__(self):
        rator = self.cursor.__iter__()
        return IteratorWrapper(rator, remember=self)

    def __del__(self):
        if self.connection.unread_result:
            self.connection.get_rows()
        self.cursor.close()
        self.connection.commit()  # no damage if rollback happened
        self.connection.close()


class MySQLMixin(object):

    def __init__(self, host, port, database, user, password, pool_name, pool_size=5):
        self.pool = pooling.MySQLConnectionPool(pool_name=pool_name, pool_size=pool_size,
                                                host=host, port=port,
                                                user=user, password=password)

        self._execute('create database if not exists %s' % self.escape(database))
        self.pool.set_config(database=database)

    @property
    def dbcur(self):
        conn = self.pool.get_connection()
        cur = conn.cursor()
        return CleaningCursor(cur, conn)


class SplitTableMixin(object):
    UPDATE_PROJECTS_TIME = 10 * 60

    def _tablename(self, project):
        if self.__tablename__:
            return '%s_%s' % (self.__tablename__, project)
        else:
            return project

    @property
    def projects(self):
        if time.time() - getattr(self, '_last_update_projects', 0) \
                > self.UPDATE_PROJECTS_TIME:
            self._list_project()
        return self._projects

    @projects.setter
    def projects(self, value):
        self._projects = value

    def _list_project(self):
        self._last_update_projects = time.time()
        self.projects = set()
        if self.__tablename__:
            prefix = '%s_' % self.__tablename__
        else:
            prefix = ''
        for project, in self._execute('show tables;'):
            if project.startswith(prefix):
                project = project[len(prefix):]
                self.projects.add(project)

    def drop(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        tablename = self._tablename(project)
        self._execute("DROP TABLE %s" % self.escape(tablename))
        self._list_project()
