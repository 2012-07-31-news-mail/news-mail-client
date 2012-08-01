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

import itertools, base64, json, datetime
from tornado import ioloop, stack_context, gen
from . import get_items, async_http_request_helper

DEFAULT_CONC = 2
DEFAULT_DELAY = 0.0

def i_string_encode(s):
    if not s:
        return ''
    
    if not isinstance(s, unicode) and not isinstance(s, str):
        s = unicode(s)
    
    if isinstance(s, unicode):
        s = s.encode('UTF-8', 'replace')
    
    b = base64.b64encode(s)
    i = '=?utf-8?B?%s?=' % b
    
    return i

def base64_data(s):
    if not s:
        return ''
    
    if not isinstance(s, unicode) and not isinstance(s, str):
        s = unicode(s)
    
    if isinstance(s, unicode):
        s = s.encode('UTF-8', 'replace')
    
    b = base64.b64encode(s)
    
    return b

def apply_format(format, msg):
    if format is None or format == 'br_html':
        msg = '<br />'.join(msg.split('\n'))
        return 'text/html;charset=utf-8', msg
    elif format == 'html':
        return 'text/html;charset=utf-8', msg
    elif format == 'text':
        return 'text/plain;charset=utf-8', msg
    else:
        raise NotImplementedError

@gen.engine
def news_mail_thread(url, key, to_iter, subject_iter, msg_iter,
            format=None, conc=None, delay=None, on_finish=None):
    to_iter = iter(to_iter)
    subject_iter = iter(subject_iter)
    msg_iter = iter(msg_iter)
    on_finish = stack_context.wrap(on_finish)
    
    if delay is None:
        delay = DEFAULT_DELAY
    
    for to in to_iter:
        subject = next(subject_iter)
        msg = next(msg_iter)
        content_type, msg_data = apply_format(format, msg)
        headers = [
            'Content-Type: %s' % content_type,
            'Content-Transfer-Encoding: base64',
        ]
        headers_data = '\r\n'.join(headers)
        
        if not subject:
            subject = '(no subject)'
        
        print '%s: opening...' % to
        
        if delay:
            delay_wait_key = object()
            ioloop.IOLoop.instance().add_timeout(
                    datetime.timedelta(seconds=delay),
                    (yield gen.Callback(delay_wait_key)),
                    )
            yield gen.Wait(delay_wait_key)
        
        req_wait_key = object()
        async_http_request_helper.async_fetch(url, data={
            'key': key,
            'data': json.dumps({
                'mail': {
                    'to': to,
                    'subject': i_string_encode(subject),
                    'message': base64_data(msg_data),
                    'headers': headers_data,
                },
            }),
        }, callback=(yield gen.Callback(req_wait_key)), use_json=True, use_raise=False)
        response, exc = (yield gen.Wait(req_wait_key))[0]
        
        if exc is None and not response.get('error'):
            print '%s: PASS' % to
        else:
            if exc is not None:
                e = exc[1]
            else:
                e = response.get('error')
            
            print '%s: ERROR: %s' % (to, e)
    
    if on_finish is not None:
        on_finish()

@gen.engine
def bulk_news_mail(url, key, to_iter, subject_iter, msg_iter,
            format=None, conc=None, delay=None, on_finish=None):
    to_iter = iter(to_iter)
    subject_iter = iter(subject_iter)
    msg_iter = iter(msg_iter)
    on_finish = stack_context.wrap(on_finish)
    
    if conc is None:
        conc = DEFAULT_CONC
    
    wait_key_list = tuple(object() for x in xrange(conc))
    
    for wait_key in wait_key_list:
        news_mail_thread(url, key, to_iter, subject_iter, msg_iter,
                format=format, conc=conc, delay=delay,
                on_finish=(yield gen.Callback(wait_key)))
    
    for wait_key in wait_key_list:
        yield gen.Wait(wait_key)
    
    if on_finish is not None:
        on_finish()

def news_mail(cfg, on_finish=None):
    on_finish = stack_context.wrap(on_finish)
    
    if cfg.count is not None and cfg.count == 'infinite':
        to_iter = get_items.get_random_infinite_items(cfg.to_items)
    elif cfg.count is not None:
        count = int(cfg.count)
        to_iter = itertools.islice(get_items.get_random_infinite_items(cfg.to_items), count)
    else:
        to_iter = get_items.get_random_finite_items(cfg.to_items)
    
    subject_iter = get_items.get_random_infinite_items(cfg.subject_items)
    msg_iter = get_items.get_random_infinite_items(cfg.msg_items)
    
    bulk_news_mail(cfg.url, cfg.key, to_iter, subject_iter, msg_iter,
            format=cfg.format, conc=cfg.conc, delay=cfg.delay,
            on_finish=on_finish)
