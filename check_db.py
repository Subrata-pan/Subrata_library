from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/kitabghar.db'
db.init_app(app)

with app.app_context():
    from sqlalchemy import text
    result = db.session.execute(text('PRAGMA table_info(ebook);'))
    columns = [row[1] for row in result.fetchall()]
    print('Columns in ebook table:', columns)
    print('cover column exists:', 'cover' in columns)
