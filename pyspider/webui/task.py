#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-16 15:30:57

import socket
import datetime
import hashlib
from flask import abort, render_template, request, json, jsonify

from pyspider.libs import utils
from .app import app


@app.route('/task/<taskid>')
def task(taskid):
    if ':' not in taskid:
        abort(400)
    project, taskid = taskid.split(':', 1)

    taskdb = app.config['taskdb']
    task = taskdb.get_task(project, taskid)
    if not task:
        abort(404)
    resultdb = app.config['resultdb']
    if resultdb:
        result = resultdb.get(project, taskid)

    if request.args.get('format', '') == 'json':
        table = taskdb._tablename(project)
        after = [x for x in taskdb._select(table, 'count(*)',
                 'lastcrawltime > %f' % task['lastcrawltime'])]
        task['tasks_after'] = after[0][0]
        return json.jsonify(task)
    else:
        return render_template("task.html", task=task, json=json, result=result,
                               status_to_string=app.config['taskdb'].status_to_string)

@app.route('/tasks/<project>/new')
def new_task(project):
    task = {
        'project': project,
        'process': {
            'callback': request.args['callback']
        },
        'schedule': {
            'age': 0,
            'force_update': True
        },
        'url': request.args['url'],
        'taskid': hashlib.sha1(project + datetime.datetime.now().ctime()).hexdigest()
    }

    rpc = app.config['scheduler_rpc']
    rpc.newtask(task)

    return jsonify(task)

@app.route('/task/<taskid>/resubmit')
def submit_task(taskid):
    if ':' not in taskid:
        abort(400)
    project, taskid = taskid.split(':')

    taskdb = app.config['taskdb']
    task = taskdb.get_task(project, taskid)
    if not task:
        abort(404)

    rpc = app.config['scheduler_rpc']
    rpc.newtask(task)

    return jsonify(task)


@app.route('/tasks')
def tasks():
    rpc = app.config['scheduler_rpc']
    taskdb = app.config['taskdb']
    project = request.args.get('project', "")
    limit = int(request.args.get('limit', 100))

    try:
        updatetime_tasks = rpc.get_active_tasks(project, limit)
    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return 'connect to scheduler error', 502

    tasks = {}
    result = []
    for updatetime, task in sorted(updatetime_tasks , key=lambda x: x[0]):
        key = '%(project)s:%(taskid)s' % task
        task['updatetime'] = updatetime
        if key in tasks and tasks[key].get('status', None) != taskdb.ACTIVE:
            result.append(tasks[key])
        tasks[key] = task
    result.extend(tasks.values())

    return render_template(
        "tasks.html",
        tasks=result,
        status_to_string=taskdb.status_to_string
    )


@app.route('/active_tasks')
def active_tasks():
    rpc = app.config['scheduler_rpc']
    taskdb = app.config['taskdb']
    project = request.args.get('project', "")
    limit = int(request.args.get('limit', 100))

    try:
        tasks = rpc.get_active_tasks(project, limit)
    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return '{}', 502, {'Content-Type': 'application/json'}

    result = []
    for updatetime, task in tasks:
        task['updatetime'] = updatetime
        task['updatetime_text'] = utils.format_date(updatetime)
        if 'status' in task:
            task['status_text'] = taskdb.status_to_string(task['status'])
        result.append(task)

    return json.dumps(result), 200, {'Content-Type': 'application/json'}

app.template_filter('format_date')(utils.format_date)
