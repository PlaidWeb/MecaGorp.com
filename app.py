""" Main Publ application """
# pylint:disable=import-outside-toplevel

import logging
import logging.handlers
import os
import os.path
import re

import arrow
import authl.flask
import flask
import publ
import werkzeug.exceptions
from flask_github_webhook import GithubWebhook
from werkzeug.middleware.proxy_fix import ProxyFix

if os.path.isfile('logging.conf'):
    logging.config.fileConfig('logging.conf')
else:
    try:
        os.makedirs('logs')
    except FileExistsError:
        pass
    logging.basicConfig(level=logging.INFO,
                        handlers=[
                            logging.handlers.TimedRotatingFileHandler(
                                'logs/publ.log', when='D'),
                            logging.StreamHandler()
                        ],
                        format="%(asctime)s %(levelname)s:%(threadName)s:%(name)s:%(message)s")

LOGGER = logging.getLogger(__name__)
LOGGER.info("Setting up")

APP_PATH = os.path.dirname(os.path.abspath(__file__))

config = {
    'database_config': {
        'provider': 'sqlite',
        'filename': os.path.join(APP_PATH, 'index.db')
    },
    'timezone': 'US/Pacific',
    'cache': {
        'CACHE_TYPE': 'memcached',
        'CACHE_DEFAULT_TIMEOUT': 86413,
        'CACHE_THRESHOLD': 500,
        'CACHE_KEY_PREFIX': 'mecagorp.com',
    } if not os.environ.get('FLASK_DEBUG') else {},

    'index_rescan_interval': 86400,
    'index_enable_watchdog': bool(os.environ.get('FLASK_DEBUG')),

    'auth': {
        'AUTH_FORCE_HTTPS': not os.environ.get('FLASK_DEBUG'),

        'SMTP_HOST': 'localhost',
        'SMTP_PORT': 25,
        'EMAIL_FROM': 'nobody@mecagorp.com',
        'EMAIL_SUBJECT': 'Sign in to mecagorp.com',

        'FEDIVERSE_NAME': 'mecagorp',
        'FEDIVERSE_HOMEPAGE': 'https://mecagorp.com/',

        'INDIEAUTH_CLIENT_ID': authl.flask.client_id,

        'TEST_ENABLED': os.environ.get('FLASK_DEBUG'),
    },

    'auth_log_prune_age': 86400 * 90,

    'search_index': 'search',
}

if not os.path.isfile('.sessionkey'):
    import uuid
    with open('.sessionkey', 'w', encoding='utf-8') as file:
        file.write(str(uuid.uuid4()))
    os.chmod('.sessionkey', 0o600)
with open('.sessionkey', encoding='utf-8') as file:
    config['secret_key'] = file.read()

app = publ.Publ(__name__, config)
app.config['GITHUB_WEBHOOK_ENDPOINT'] = '/_gh'
app.config['GITHUB_WEBHOOK_SECRET'] = os.environ.get('GITHUB_SECRET')

hooks = GithubWebhook(app)


@hooks.hook()
def deploy(data):
    """ Called when GitHub gets an update """
    import subprocess
    import threading

    LOGGER.info("Got github hook with data: %s", data)

    try:
        result = subprocess.check_output(
            ['./deploy.sh', 'nokill'],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        LOGGER.error("Deployment failed: %s", err.output)
        return flask.Response(err.output, status=500, mimetype='text/plain')

    def restart_server():
        LOGGER.info("Restarting")
        subprocess.run(['systemctl', '--user', 'restart',
                       'novembeat.com'], check=True)

    LOGGER.info("Restarting server in 3 seconds...")
    threading.Timer(3, restart_server).start()

    return flask.Response(result, mimetype='text/plain')


def keymaster(sid):
    """ Generates a salted token for the browser """
    import hashlib

    parts = [
        str(sid),
        flask.request.remote_addr,
        flask.request.headers.get('User-Agent')
    ]
    token = hashlib.md5('|'.join(parts).encode('utf-8'))
    return token.digest()


@app.template_filter('hashtag')
def make_hashtag(words: str):
    words = words.replace("'", '')
    words_list = re.split(r'[^a-zA-Z0-9]+', words)

    return ''.join([w.title() if w.islower() else w for w in words_list])


@app.before_request
def antiscraper():
    """ Dissuade aggressive bots from pummeling the site """

    # Don't fire for login callbacks
    if flask.request.path.startswith('/_cb/'):
        return

    if '&amp;' in flask.request.url:
        raise werkzeug.exceptions.BadRequest(
            "learn how HTML entities work, you stupid bot")

    # Logged-in users have passed the test already
    if publ.user.get_active():
        return

    if 'sid' in flask.request.args:
        # definitely a URL that didn't come from here
        raise werkzeug.exceptions.Unauthorized("y'all")

    # Send possible crawlers to the login page
    score = len(list(flask.request.args.items(True)))
    if score > 1:
        # Check for an existing sentience token
        try:
            sid, token = flask.session['vinz']
            if (arrow.now().shift(hours=-1) < arrow.get(float(sid)) < arrow.now() and
                    keymaster(sid) == token):
                return
        except (KeyError, ValueError, arrow.ParserError):
            pass

        raise werkzeug.exceptions.TooManyRequests("Sentience test")

    # remove old cruft from the session
    for key in ('sid', 'addr', 'ua'):
        if key in flask.session:
            flask.session.pop(key)

    return


@app.route('/_zuul', methods=['POST'])
def gatekeeper():
    """ Check the test response and set the salted token upon passing """

    try:
        sid = float(flask.request.form['sid'])
        if arrow.get(sid) > arrow.now():
            # Someone's trying to set a token that'll last longer
            raise werkzeug.exceptions.BadRequest("Hello time traveler")
        if arrow.get(sid) < arrow.now().shift(minutes=-5):
            # Someone took a while to respond to the form
            raise werkzeug.exceptions.TooManyRequests("Try again")
    except ValueError as exc:
        raise werkzeug.exceptions.BadRequest("Nice try") from exc

    redir = flask.request.form['redir']
    flask.session['vinz'] = sid, keymaster(sid)
    return flask.redirect(f'{redir}', code=303)


@app.after_request
def add_webmention_endpoint(response):
    """ publish webmention endpoint for everything, including error pages and resources """
    response.headers.add(
        'link', '<https://webmention.io/beesbuzz.biz/webmention>; rel="webmention"')

    return response


app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
