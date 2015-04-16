# Gunicorn
# ========
bind = '127.0.0.1:5000'

# Muffin
# ======

PLUGINS = (

    # Contrib plugins
    'muffin_jade',
    'muffin_peewee',
    'muffin_session',
    'muffin_oauth',

    'invalid.plugin',
)

STATIC_ROOT = 'example/static'

# Plugin options
# ==============

SESSION_SECRET = 'SecretHere'
JADE_TEMPLATE_FOLDERS = 'example/templates',
OAUTH_CLIENTS = {
    'github': {
        'client_id': 'b6281b6fe88fa4c313e6',
        'client_secret': '21ff23d9f1cad775daee6a38d230e1ee05b04f7c',
    }
}
PEEWEE_MIGRATIONS_PATH = 'example/migrations'
