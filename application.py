from flask import Flask
from flask_mongoengine import MongoEngine
from flask_wtf.csrf import CSRFProtect

import os

db = MongoEngine()
csrf = CSRFProtect()


def create_app(**config_overrides):
    app = Flask(__name__)

    app.config.from_pyfile('settings.py')
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = '1'
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = '1'
    app.config.update(config_overrides)

    csrf.init_app(app)
    db.init_app(app)
    from g_oauth.views import o_bp, google_bp
    app.register_blueprint(o_bp)
    app.register_blueprint(google_bp, url_prefix='/google_login')
    from user.views import user_app
    app.register_blueprint(user_app)
    from stores.views import store_app
    app.register_blueprint(store_app)
    from core.views import core
    app.register_blueprint(core)
    from admin_tool.views import console_app
    app.register_blueprint(console_app)
    return app
