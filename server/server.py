from flask import Flask
from db_model import db, init_db, init_db_command
import os
import logging


def configure_logging():
    FORMAT = '%(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    db_url = os.environ.get("DATABASE_URL")

    if db_url is None:
        # default to a sqlite database in the instance folder
        db_url = f'sqlite:///{os.path.join(app.instance_path, "base.db")}'
        # ensure the instance folder exists
        os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    db.init_app(app)
    with app.app_context():
        init_db()
    app.cli.add_command(init_db_command)
    configure_logging()

    from routes import bp
    app.register_blueprint(bp, url_prefix='/protocols')

    return app


HOST = "0.0.0.0"
DEBUG = True


def main():
    app = create_app()
    app = app.run(host=HOST, port=8080, debug=DEBUG)
    # app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
