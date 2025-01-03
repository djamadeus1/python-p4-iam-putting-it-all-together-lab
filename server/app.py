#!/usr/bin/env python3
import sys
sys.setrecursionlimit(1500)

from flask import Flask, jsonify, request, session
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS

from config import app, db, api
from models import User, Recipe

CORS(app, supports_credentials=True)  # Enable CORS with credentials support

@app.before_request
def clear_session_on_startup():
    if not session.get("cleared"):
        session.clear()
        session["cleared"] = True  # Prevent repeated clearing in the same session
        print("Session cleared on server startup.")

# Signup Resource
class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        image_url = data.get("image_url")
        bio = data.get("bio")

        if not username or not password:
            return {"error": "Username and password are required"}, 400

        try:
            new_user = User(username=username, image_url=image_url, bio=bio)
            new_user.password = password  # Hash the password
            db.session.add(new_user)
            db.session.commit()

            session["user_id"] = new_user.id
            return {
                "id": new_user.id,
                "username": new_user.username,
                "image_url": new_user.image_url,
                "bio": new_user.bio,
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {"error": "Username already exists"}, 400

        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}, 500

# CheckSession Resource
class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")
        if user_id:
            user = User.query.get(user_id)
            if user:
                return {"id": user.id, "username": user.username}, 200
        return {"error": "Unauthorized"}, 401

# Login Resource
class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {"error": "Username and password are required."}, 400

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return {"message": "Login successful"}, 200

        return {"error": "Invalid credentials"}, 401

# Logout Resource
class Logout(Resource):
    def post(self):
        session.clear()
        return {"message": "Logged out"}, 200
    
    def delete(self):
        session.clear()
        return {"message": "Logged out"}, 200

# RecipeIndex Resource
class RecipeIndex(Resource):
    def get(self):
        try:
            recipes = Recipe.query.all()
            return [recipe.to_dict() for recipe in recipes], 200
        except Exception as e:
            return {"error": str(e)}, 500

    def post(self):
        if "user_id" not in session:
            return {"error": ["Unauthorized. Please log in first."]}, 401

        data = request.get_json()
        title = data.get("title")
        instructions = data.get("instructions")
        minutes_to_complete = data.get("minutes_to_complete")

        if not title or not instructions or len(instructions) < 50 or not minutes_to_complete:
            return {"error": ["Invalid recipe data. Ensure all fields are filled and instructions are at least 50 characters long."]}, 422

        try:
            user_id = session.get("user_id")

            new_recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id
            )
            db.session.add(new_recipe)
            db.session.commit()

            return {
                "id": new_recipe.id,
                "title": new_recipe.title,
                "instructions": new_recipe.instructions,
                "minutes_to_complete": new_recipe.minutes_to_complete,
                "user": {"id": new_recipe.user.id, "username": new_recipe.user.username}
            }, 201

        except IntegrityError as e:
            db.session.rollback()
            return {"error": [f"Integrity error: {str(e)}"]}, 400

        except Exception as e:
            db.session.rollback()
            return {"error": [f"An unexpected error occurred: {str(e)}"]}, 500

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Flask API!"})

# Registering resources
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', methods=['GET', 'POST'], endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)