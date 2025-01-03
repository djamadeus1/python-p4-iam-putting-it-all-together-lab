from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from config import db, bcrypt


class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    # Columns
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, default="https://via.placeholder.com/150")
    bio = db.Column(db.String)

    # Relationships
    recipes = db.relationship("Recipe", backref="user", cascade="all, delete-orphan")

    # Serialization Rules to prevent recursion
    serialize_rules = ('-recipes.user',)

    # Password property
    @hybrid_property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, password):
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """Authenticate the user by comparing the hash."""
        return bcrypt.check_password_hash(self._password_hash, password)

    # Validation
    @validates("username")
    def validate_username(self, key, username):
        if not username:
            raise ValueError("Username is required.")
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        return username

    @validates("image_url")
    def validate_image_url(self, key, image_url):
        if not image_url:
            return "https://via.placeholder.com/150"  # Default image
        return image_url


class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    # Columns
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)

    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Serialization Rules to prevent recursion
    serialize_rules = ('-user.recipes',)

    # Validation
    @validates("title", "instructions")
    def validate_fields(self, key, value):
        if not value:
            raise ValueError(f"{key.capitalize()} is required.")
        if key == "instructions" and len(value) < 50:
            raise ValueError("Instructions must be at least 50 characters long.")
        return value

    @validates("minutes_to_complete")
    def validate_minutes_to_complete(self, key, value):
        if value <= 0:
            raise ValueError("Minutes to complete must be greater than 0.")
        return value