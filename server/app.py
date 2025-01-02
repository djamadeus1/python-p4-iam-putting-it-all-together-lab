#!/usr/bin/env python3

from flask import Flask, jsonify, request, session
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

@app.before_request
def clear_session_on_startup():
    if not session.get("cleared"):
        session.clear()
        session["cleared"] = True  # Prevent repeated clearing in the same session
        print("Session cleared on server startup.")


class Signup(Resource):
    def post(self):
        # Get JSON data from the request
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        image_url = data.get("image_url")
        bio = data.get("bio")

        # Validate input data
        if not username or not password:
            return {"error": "Username and password are required"}, 400

        try:
            # Create a new user instance
            new_user = User(username=username, image_url=image_url, bio=bio)
            new_user.password = password  # Use the password setter to hash the password
            
            # Save user to the database
            db.session.add(new_user)
            db.session.commit()

            # Add user_id to the session
            session["user_id"] = new_user.id

            # Return success response with 201 status
            return {
                "id": new_user.id,
                "username": new_user.username,
                "image_url": new_user.image_url,
                "bio": new_user.bio,
            }, 201

        except IntegrityError:
            db.session.rollback()
            # Handle duplicate username error
            return {"error": "Username already exists"}, 400

        except Exception as e:
            # Handle unexpected errors
            return {"error": f"An unexpected error occurred: {str(e)}"}, 500

class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")
        if user_id:
            user = User.query.get(user_id)
            if user:
                return {"id": user.id, "username": user.username}, 200
        return {"error": "Unauthorized"}, 401

class Login(Resource):
    def post(self):
        # Example login logic
        data = request.get_json()

        # Check if username or password is missing
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return {"error": "Username and password are required."}, 400

        # Query for the user in the database
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return {"message": "Login successful"}, 200

        # Handle invalid credentials
        return {"error": "Invalid credentials"}, 401

class Logout(Resource):
    def post(self):
        session.clear()
        return {"message": "Logged out"}, 200
    
    def delete(self):
        session.clear()
        return {"message": "Logged out"}, 200

class RecipeIndex(Resource):
    def get(self):
        # Check if the user is logged in
        if "user_id" not in session:
            return {"error": "Unauthorized"}, 401

        # Query all recipes from the database
        recipes = Recipe.query.all()

        return [
            {
                "id": recipe.id,
                "title": recipe.title,
                "instructions": recipe.instructions,
                "minutes_to_complete": recipe.minutes_to_complete,
                "user": {
                    "id": recipe.user.id,
                    "username": recipe.user.username
                }
            }
            for recipe in recipes
        ], 200

    def post(self):
        # Check if the user is logged in
        if "user_id" not in session:
            return {"error": "Unauthorized"}, 401

        data = request.get_json()
        title = data.get("title")
        instructions = data.get("instructions")
        minutes_to_complete = data.get("minutes_to_complete")

        # Validate input data
        if not title or not instructions or len(instructions) < 50 or not minutes_to_complete:
            return {
                "error": "Invalid recipe data. Ensure all fields are filled and instructions are at least 50 characters long."
            }, 422

        try:
            # Create a new recipe
            new_recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=session["user_id"]
            )
            db.session.add(new_recipe)
            db.session.commit()

            return {
                "id": new_recipe.id,
                "title": new_recipe.title,
                "instructions": new_recipe.instructions,
                "minutes_to_complete": new_recipe.minutes_to_complete,
                "user": {
                    "id": new_recipe.user.id,
                    "username": new_recipe.user.username
                }
            }, 201
        except Exception as e:
            db.session.rollback()
            return {"error": f"An error occurred: {str(e)}"}, 500

# Add a root route
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Flask API!"})

# Registering the resources
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)