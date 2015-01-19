#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-10 01:34:09

import os
import time
import click
import shutil
import unittest2 as unittest

from pyspider import run
from click.testing import CliRunner

class TestBench(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/bench', ignore_errors=True)
        os.makedirs('./data/bench')

    @classmethod
    def tearDownClass(self):
        shutil.rmtree('./data/bench', ignore_errors=True)

    def not_test_10_bench(self):
        self.setUpClass()
        runner = CliRunner()
        result = runner.invoke(run.cli, ['--queue-maxsize=0',
                                         'bench', '--run-in=thread', '--total=500'])
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('Crawled', result.output)
        self.assertIn('Fetched', result.output)
        self.assertIn('Processed', result.output)
        self.assertIn('Saved', result.output)
        print(result.output)
        self.tearDownClass()
