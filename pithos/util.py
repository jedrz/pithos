# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
### BEGIN LICENSE
# Copyright (C) 2010-2012 Kevin Mehall <km@kevinmehall.net>
#This program is free software: you can redistribute it and/or modify it 
#under the terms of the GNU General Public License version 3, as published 
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along 
#with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import logging
import webbrowser
from urllib.parse import splittype, splituser, splitpasswd
import urllib.request
import http.client
import ssl

def parse_proxy(proxy):
    """ _parse_proxy from urllib """
    scheme, r_scheme = splittype(proxy)
    if not r_scheme.startswith("/"):
        # authority
        scheme = None
        authority = proxy
    else:
        # URL
        if not r_scheme.startswith("//"):
            raise ValueError("proxy URL with no authority: %r" % proxy)
        # We have an authority, so for RFC 3986-compliant URLs (by ss 3.
        # and 3.3.), path is empty or starts with '/'
        end = r_scheme.find("/", 2)
        if end == -1:
            end = None
        authority = r_scheme[2:end]
    userinfo, hostport = splituser(authority)
    if userinfo is not None:
        user, password = splitpasswd(userinfo)
    else:
        user = password = None
    return scheme, user, password, hostport

# based on https://github.com/Anorov/PySocks/blob/master/sockshandler.py
class SocksiPyConnection(http.client.HTTPConnection):

    def __init__(self, proxy_type=None, addr=None, port=None, rdns=True, username=None, password=None, *args, **kwargs):
        self.proxy_args = (proxy_type, addr, port, rdns, username, password)
        super().__init__(*args, **kwargs)

    def connect(self):
        import socks
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.proxy_args)
        if type(self.timeout) in (int, float):
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

class SocksiPyConnectionS(http.client.HTTPSConnection):

    def __init__(self, proxy_type=None, addr=None, port=None, rdns=True, username=None, password=None, *args, **kwargs):
        self.proxy_args = (proxy_type, addr, port, rdns, username, password)
        super().__init__(*args, **kwargs)

    def connect(self):
        import socks
        sock = socks.socksocket()
        sock.setproxy(*self.proxy_args)
        if type(self.timeout) in (int, float):
            sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file)

class SocksiPyHandler(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):

    def __init__(self, proxy_type=None, addr=None, port=None, rdns=True, username=None, password=None, *args, **kwargs):
        self.proxy_type = proxy_type
        self.addr = addr
        self.port = port
        self.rdns = rdns
        self.username = username
        self.password = password
        super().__init__(*args, **kwargs)

    def http_open(self, req):
        return self._do_open(req, SocksiPyConnection)

    def https_open(self, req):
        return self._do_open(req, SocksiPyConnectionS)

    def _do_open(self, req, conn_class):
        def build(*args, **kwargs):
            conn = conn_class(
                self.proxy_type, self.addr, self.port, self.rdns, self.username, self.password,
                *args, **kwargs
            )
            return conn
        return self.do_open(build, req)

def open_browser(url):
    logging.info("Opening URL {}".format(url))
    webbrowser.open(url)
    if isinstance(webbrowser.get(), webbrowser.BackgroundBrowser):
        try:
            os.wait() # workaround for http://bugs.python.org/issue5993
        except:
            pass
