from flask import Flask
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Initialize Flask app
app = Flask(__name__)

# App configuration
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'  # Ensure this is kept secret
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Path to your database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False       # Avoid unnecessary overhead
app.json.compact = False                                   # Enable compact JSON responses

# Set up naming conventions for migrations
metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

# Initialize SQLAlchemy with metadata
db = SQLAlchemy(metadata=metadata)
db.init_app(app)

# Initialize Flask-Migrate for database migrations
migrate = Migrate(app, db)

# Initialize Flask-Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Initialize Flask-Restful for API resources
api = Api(app)