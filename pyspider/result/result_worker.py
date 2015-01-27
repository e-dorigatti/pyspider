#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-19 15:37:46

import time
import json
import logging
import hashlib
import itertools
from six.moves import queue as Queue
from pyspider.libs.utils import utf8

logger = logging.getLogger("result")


class ResultWorker(object):

    """
    do with result
    override this if needed.
    """

    def __init__(self, resultdb, inqueue):
        self.resultdb = resultdb
        self.inqueue = inqueue
        self._quit = False

    def on_result(self, task, result):
        '''Called every result'''
        if not result:
            return
        if 'taskid' in task and 'project' in task and 'url' in task:
            logger.info('result %s:%s %s -> %.30r' % (
                task['project'], task['taskid'], task['url'], result))
            return self.resultdb.save(
                project=task['project'],
                taskid=task['taskid'],
                url=task['url'],
                result=result
            )
        else:
            logger.warning('result UNKNOW -> %.30r' % result)
            return

    def quit(self):
        self._quit = True

    def run(self):
        '''Run loop'''
        logger.info("result_worker starting...")

        while not self._quit:
            try:
                task, result = self.inqueue.get(timeout=1)
                self.on_result(task, result)
            except Queue.Empty as e:
                continue
            except KeyboardInterrupt:
                break
            except AssertionError as e:
                logger.error(e)
                continue
            except Exception as e:
                logger.exception(e)
                continue

        logger.info("result_worker exiting...")


class OneResultWorker(ResultWorker):
    '''Result Worker for one mode, write results to stdout'''
    def on_result(self, task, result):
        '''Called every result'''
        if not result:
            return
        if 'taskid' in task and 'project' in task and 'url' in task:
            logger.info('result %s:%s %s -> %.30r' % (
                task['project'], task['taskid'], task['url'], result))
            print(json.dumps({
                'taskid': task['taskid'],
                'project': task['project'],
                'url': task['url'],
                'result': result,
                'updatetime': time.time()
            }))
        else:
            logger.warning('result UNKNOW -> %.30r' % result)
            return


class TimestampedResultWorker(ResultWorker):
    """ ResultWorker that keeps track of useful timestamps inside the
    items stored in ResultDB. More specifically:
    1) created: when was the item first scraped?
    2) modified: when was the item last modified (with at least one item value changed)?
    3) visited: when was the item last scraped (with or without changes)?
    """
    CREATED_FIELD_NAME = '_created'
    MODIFIED_FIELD_NAME = '_modified'
    VISITED_FIELD_NAME = '_visited'

    def on_result(self, task, result):
        if 'taskid' in task and 'project' in task:
            project = task['project']
            taskid = task['taskid']

            visited = time.time()
            created = visited
            modified = visited

            old_result = self.resultdb.get(project, taskid)
            if old_result:
                created = old_result.get(self.CREATED_FIELD_NAME)  # if not there, leave it empty as we don't know when this item was first created
                if self._objs_differ(result, old_result):
                    modified = visited

            result[self.CREATED_FIELD_NAME] = created
            result[self.MODIFIED_FIELD_NAME] = modified
            result[self.VISITED_FIELD_NAME] = visited

        return super(TimestampedResultWorker, self).on_result(task, result)

    @classmethod
    def _objs_differ(cls, obj1, obj2):
        for key in itertools.chain(obj1.keys(), obj2.keys()):
            if key == cls.CREATED_FIELD_NAME \
                    or key == cls.MODIFIED_FIELD_NAME \
                    or key == cls.VISITED_FIELD_NAME:
                continue
            if key not in obj1 or key not in obj2 or obj1[key] != obj2[key]:
                return False
        return True


class CustomPKResultWorker(ResultWorker):
    """ ResultWorker that allows to store items based on their own
    primary keys, therefore allowing:
    1) multiple items returned from the same task;
    2) an item to be returned from different tasks.
    For this to work, each item should define its own 'pk' field, which
    will be removed from the item itself before being stored in the resultdb.

    Please notice that this will break the pyspider UI, as this will override
    the taskid right before storing the result in the database, and therefore
    won't be retrieved by taskid; this is expected, as after this changes
    a one-to-one relationship between tasks and items is replaced in favor of a
    many-to-one.
    """
    PK_FIELD_NAME = 'pk'

    def on_result(self, task, result):
        if result and self.PK_FIELD_NAME in result:
            task['taskid'] = self._deep_hash(result.pop(self.PK_FIELD_NAME))
        return super(CustomPKResultWorker, self).on_result(task, result)

    @staticmethod
    def _deep_hash(something):
        if isinstance(something, (list, tuple)):
            key = u', '.join(
                CustomPKResultWorker._deep_hash(x)
                for x in something
            )
        elif isinstance(something, set):
            key = u', '.join(
                CustomPKResultWorker._deep_hash(x)
                for x in sorted(something)
            )
        elif isinstance(something, dict):
            key = u', '.join(
                u'{}:{}'.format(k, CustomPKResultWorker._deep_hash(v))
                for k, v in sorted(something.iteritems())
            )
        else:
            key = u'{}'.format(something)
        return hashlib.sha1(utf8(key)).hexdigest()


class TimestampedCustomPKResultWorker(CustomPKResultWorker,
                                      TimestampedResultWorker):
    pass
