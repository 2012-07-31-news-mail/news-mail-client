# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2012 Andrej A Antonov <polymorphm@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

assert unicode is not str
assert str is bytes

import argparse, ConfigParser, sys, os.path
from tornado import ioloop
from .news_mail import news_mail

class UserError(Exception):
    pass

class Config(object):
    pass

def final():
    print(u'done!')
    ioloop.IOLoop.instance().stop()

def main():
    parser = argparse.ArgumentParser(
            description=
                    u'client part for `news-mail` project. '
                    u'sending news for blogs through mail.')
    parser.add_argument('cfg', metavar='CONFIG-FILE',
            help=u'config file for task\'s process')
    
    args = parser.parse_args()
    config = ConfigParser.ConfigParser()
    config.read(args.cfg)
    
    cfg = Config()
    
    cfg_section = 'news-mail-client'
    cfg_dir = os.path.dirname(args.cfg).decode(sys.getfilesystemencoding())
    
    cfg.url = config.get(cfg_section, 'url').decode('utf-8', 'replace') \
            if config.has_option(cfg_section, 'url') else None
    cfg.key = config.get(cfg_section, 'key').decode('utf-8', 'replace') \
            if config.has_option(cfg_section, 'key') else None
    cfg.to_items = os.path.join(
                cfg_dir,
                config.get(cfg_section, 'to-items').decode('utf-8', 'replace')
            ) if config.has_option(cfg_section, 'to-items') else None
    cfg.msg_items = os.path.join(
                cfg_dir,
                config.get(cfg_section, 'msg-items').decode('utf-8', 'replace')
            ) if config.has_option(cfg_section, 'msg-items') else None
    cfg.subject_items = os.path.join(
                cfg_dir,
                config.get(cfg_section, 'subject-items').decode('utf-8', 'replace')
            ) if config.has_option(cfg_section, 'subject-items') else None
    cfg.format = config.get(cfg_section, 'format').decode('utf-8', 'replace') \
            if config.has_option(cfg_section, 'format') else None
    cfg.count = config.get(cfg_section, 'count').decode('utf-8', 'replace') \
            if config.has_option(cfg_section, 'count') else None
    cfg.conc = int(config.get(cfg_section, 'conc').decode('utf-8', 'replace')) \
            if config.has_option(cfg_section, 'conc') else None
    cfg.delay = float(config.get(cfg_section, 'delay').decode('utf-8', 'replace')) \
            if config.has_option(cfg_section, 'delay') else None
    
    if cfg.to_items is None:
        raise UserError('cfg.to_items is None')
    if cfg.msg_items is None:
        raise UserError('cfg.msg_items is None')
    
    news_mail(cfg, on_finish=final)
    
    ioloop.IOLoop.instance().start()
