from sqlalchemy.dialects.sqlite import JSON
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext
import click

db = SQLAlchemy()


class Session(db.Model):
    session_token = db.Column(db.String, primary_key=True)
    payload = db.Column(JSON, nullable=False)


class Keys(db.Model):
    session_token = db.Column(db.String, primary_key=True)
    key_idx = db.Column(db.Integer, primary_key=True)
    key0_val = db.Column(db.String)
    key1_val = db.Column(db.String)


def init_db():
    db.drop_all()
    db.create_all()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
