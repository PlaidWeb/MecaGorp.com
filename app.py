""" Main Publ application """

import logging
import logging.handlers
import os
import os.path

import authl.flask
import publ
from flask_github_webhook import GithubWebhook

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
    import threading
    import subprocess

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

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
