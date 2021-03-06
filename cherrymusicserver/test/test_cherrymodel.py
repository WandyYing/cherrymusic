#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner
#
# Project page:
#   http://fomori.org/cherrymusic/
# Sources on github:
#   http://github.com/devsnd/cherrymusic/
#
# CherryMusic is based on
#   jPlayer (GPL/MIT license) http://www.jplayer.org/
#   CherryPy (BSD license) http://www.cherrypy.org/
#
# licensed under GNU GPL version 3 (or later)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

import nose
import os

from mock import *
from nose.tools import *

from collections import defaultdict

from cherrymusicserver import log
log.setTest()

import cherrymusicserver as cherry

from cherrymusicserver import cherrymodel

def cherryconfig(cfg=None):
    from cherrymusicserver import configuration
    cfg = cfg or {}
    c = configuration.from_defaults()
    c = c.update({'media.basedir': os.path.join(os.path.dirname(__file__), 'data_files')})
    c = c.update(cfg)
    return c


@patch('cherrymusicserver.cherrymodel.cherry.config', cherryconfig())
@patch('cherrymusicserver.cherrymodel.os')
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
@patch('cherrymusicserver.cherrymodel.isplayable', lambda _: True)
def test_hidden_names_listdir(cache, os):
    model = cherrymodel.CherryModel()
    os.path.join = lambda *a: '/'.join(a)

    content = ['.hidden']
    cache.listdir.return_value = content
    os.listdir.return_value = content
    assert not model.listdir('')

    content = ['not_hidden.mp3']
    cache.listdir.return_value = content
    os.listdir.return_value = content
    assert model.listdir('')


@patch('cherrymusicserver.cherrymodel.cherry.config', cherryconfig({'search.maxresults': 10}))
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
@patch('cherrymusicserver.cherrymodel.cherrypy')
def test_hidden_names_search(cherrypy, cache):
    model = cherrymodel.CherryModel()

    cache.searchfor.return_value = [cherrymodel.MusicEntry('.hidden.mp3', dir=False)]
    assert not model.search('something')

    cache.searchfor.return_value = [cherrymodel.MusicEntry('not_hidden.mp3', dir=False)]
    assert model.search('something')

@patch('cherrymusicserver.cherrymodel.cherry.config', cherryconfig({'search.maxresults': 10}))
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
@patch('cherrymusicserver.cherrymodel.cherrypy')
def test_hidden_names_listdir(cherrypy, cache):
    model = cherrymodel.CherryModel()
    dir_listing = model.listdir('')
    assert len(dir_listing) == 1
    assert dir_listing[0].path == 'not_hidden.mp3'


@patch('cherrymusicserver.cherrymodel.cherry.config', cherryconfig({'media.transcode': False}))
def test_randomMusicEntries():
    model = cherrymodel.CherryModel()

    def makeMusicEntries(n):
        return [cherrymodel.MusicEntry(str(i)) for i in range(n)]

    with patch('cherrymusicserver.cherrymodel.CherryModel.cache') as mock_cache:
        with patch('cherrymusicserver.cherrymodel.CherryModel.isplayable') as mock_playable:
            mock_cache.randomFileEntries.side_effect = makeMusicEntries

            mock_playable.return_value = True
            eq_(2, len(model.randomMusicEntries(2)))

            mock_playable.return_value = False
            eq_(0, len(model.randomMusicEntries(2)))


@patch('cherrymusicserver.cherrymodel.cherry.config', cherryconfig({'media.transcode': False}))
def test_isplayable():
    model = cherrymodel.CherryModel()

    # can't use tempfile.TemporaryDirectory b/c Python2.6/3.1 compatibility
    import os, shutil, tempfile
    tempdir = tempfile.mkdtemp(suffix='_test_cherrymodel_isplayable')

    def abspath(filename):
        return os.path.join(tempdir, filename)

    def model_abspath(cls, filename):
        return abspath(filename)

    def mkfile(filename, content=''):
        fullpath = abspath(filename)
        with open(fullpath, "w") as newfile:
            if content:
                newfile.write(content)
        assert os.path.isfile(fullpath)
        return filename

    def mkdir(dirname):
        fullpath = abspath(dirname)
        os.mkdir(fullpath)
        assert os.path.isdir(fullpath)
        return dirname

    with patch('cherrymusicserver.cherrymodel.CherryModel.supportedFormats', ['mp3']):
        with patch('cherrymusicserver.cherrymodel.CherryModel.abspath', classmethod(model_abspath)):
            try:
                isplayable = model.isplayable
                assert isplayable(mkfile('ok.mp3', 'content'))
                assert not isplayable(mkfile('empty.mp3'))
                assert not isplayable(mkfile('bla.unsupported', 'content'))
                assert not isplayable(mkdir('directory.mp3'))
                assert not isplayable('inexistant')
            finally:
                shutil.rmtree(tempdir)


if __name__ == '__main__':
    nose.runmodule()
