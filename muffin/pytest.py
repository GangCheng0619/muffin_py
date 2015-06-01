# Configure your tests here
import asyncio
import io
import os

import aiohttp
import pytest
import webob
import webtest
from gunicorn import util

import muffin


def pytest_addoption(parser):
    """ Append pytest options for testing Muffin apps. """
    parser.addini('muffin_app', 'Set path to muffin application')
    parser.addoption('--muffin-app', dest='muffin_app', help='Set to muffin application')

    parser.addini('muffin_config', 'Set module path to muffin configuration')
    parser.addoption('--muffin-config', dest='muffin_config',
                     help='Set module path to muffin configuration')


def pytest_load_initial_conftests(early_config, parser, args):
    """ Prepare to loading Muffin application. """
    options = parser.parse_known_args(args)

    # Initialize configuration
    config = options.muffin_config or early_config.getini('muffin_config')
    if config:
        os.environ[muffin.CONFIGURATION_ENVIRON_VARIABLE] = config

    # Initialize application
    app = options.muffin_app or early_config.getini('muffin_app')
    early_config.app = app


def WSGIHandler(app, loop):

    def handle(environ, start_response):

        req = webob.Request(environ)
        vers = aiohttp.HttpVersion10 if req.http_version == 'HTTP/1.0' else aiohttp.HttpVersion11
        message = aiohttp.RawRequestMessage(
            req.method, req.path_qs, vers, aiohttp.CIMultiDict(req.headers), False, False)
        payload = aiohttp.StreamReader(loop=loop)
        payload.feed_data(req.body)
        payload.feed_eof()
        factory = aiohttp.web.RequestHandlerFactory(
            app, app.router, loop=loop, keep_alive_on=False)
        handler = factory()
        handler.transport = io.BytesIO()
        handler.writer = aiohttp.parsers.StreamWriter(
            handler.transport, handler, handler.reader, handler._loop)
        loop.run_until_complete(handler.handle_request(message, payload))
        handler.transport.seek(0)
        res = webob.Response.from_file(handler.transport)
        start_response(res.status[9:], res.headerlist)
        return res.app_iter

    return handle


@pytest.fixture(scope='session')
def loop(request):
    """ Create and provide asyncio loop. """
    loop = asyncio.new_event_loop()
    return loop


@pytest.fixture(scope='session')
def app(pytestconfig, request):
    """ Provide an example application. """
    app = pytestconfig.app
    if not app:
        raise SystemExit(
            'Improperly configured. Please set ``muffin_app`` in your pytest config. '
            'Or use ``--muffin-app`` command option.')
    app = util.import_app(app)
    return app


@pytest.fixture(scope='session', autouse=True)
def _initialize(app, loop, request):
    app._loop = loop
    loop.run_until_complete(app.start())

    if 'peewee' in app.plugins:
        import peewee

        for model in app.plugins.peewee.models.values():
            try:
                model.create_table()
            except peewee.OperationalError:
                pass

    @request.addfinalizer
    def finish():
        loop.run_until_complete(app.finish())
        loop.close()


@pytest.fixture(scope='function')
def client(app, loop):
    """ Prepare a tests' client. """
    app = WSGIHandler(app, loop=loop)
    client = webtest.TestApp(app)
    client.exception = webtest.AppError
    return client


@pytest.fixture(scope='function')
def db(app, request):
    """ Run tests in transaction. """
    if 'peewee' in app.plugins:
        app.ps.peewee.database.set_autocommit(False)
        app.ps.peewee.database.begin()
        request.addfinalizer(lambda: app.ps.peewee.database.rollback())
        return app.ps.peewee.database


@pytest.fixture(scope='session')
def mixer(app):
    if 'peewee' in app.plugins:
        from mixer.backend.peewee import Mixer
        return Mixer(commit=True)
