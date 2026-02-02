import os

basedir = os.getcwd()
db_path = os.path.join(basedir, 'database.db')

config = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_path,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
}