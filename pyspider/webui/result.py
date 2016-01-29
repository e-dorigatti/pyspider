#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-19 16:23:55

from __future__ import unicode_literals

from flask import render_template, request, json
from .app import app
from pyspider.libs import result_dump
import tornado.web
import tornado.ioloop


@app.route('/results')
def result():
    resultdb = app.config['resultdb']
    project = request.args.get('project')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 20))

    count = resultdb.count(project)
    results = list(resultdb.select(project, offset=offset, limit=limit))

    return render_template(
        "result.html", count=count, results=results,
        result_formater=result_dump.result_formater,
        project=project, offset=offset, limit=limit, json=json
    )


class ResultDumper(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, project, _format):
        resultdb = app.config['resultdb']

        # force update project list
        resultdb.get(project, 'any')
        if project not in resultdb.projects:
            raise tornado.web.HTTPError(404, 'No such project')

        offset = int(self.get_argument('offset', 0)) or None
        limit = int(self.get_argument('limit', 0)) or None
        results = resultdb.select(project, offset=offset, limit=limit)

        if _format == 'json':
            valid = self.get_argument('style', 'rows') == 'full'
            self.generator = result_dump.dump_as_json(results, valid)
            mimetype='application/json'
        elif _format == 'txt':
            self.generator = result_dump.dump_as_txt(results)
            mimetype='text/plain'
        elif _format == 'csv':
            self.generator = result_dump.dump_as_csv(results)
            mimetype='text/csv'
        else:
            raise tornado.web.HTTPError(404, 'Format not available, choose from json, csv, txt')

        self.set_header('Content-Type', mimetype)
        tornado.ioloop.IOLoop.current().add_callback(self.write_data)

    def write_data(self):
        try:
            data = self.generator.next()
            self.write(data)
            self.flush(callback=self.write_data)
        except StopIteration:
            self.flush()
            self.finish()
