from flask import Flask, render_template, redirect, request, session, jsonify
from flask_mongoengine import MongoEngine
import openai
import os

app = Flask(__name__)

# Flask app configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['MONGODB_SETTINGS'] = {
    'db': 'Capstone',
    'host': 'mongodb://localhost/Capstone'
}
# app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_secret_key')  # Ensure to set a strong secret key

# Initialize MongoEngine with Flask app
db = MongoEngine(app)

# Ensure API key is securely loaded from environment variables
openai.api_key = os.getenv('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')


# Database models
class NewUser(db.Document):
    name = db.StringField(required=True)
    email = db.StringField(required=True)
    username = db.StringField(required=True, unique=True)
    password = db.StringField(required=True)

    def to_json(self):
        return {
            'name': self.name,
            'email': self.email,
            'username': self.username,
            'password': self.password,  # Consider not sending back the password
        }


class Passwords(db.Document):
    user = db.ReferenceField(NewUser, required=True)
    website = db.StringField(required=True)
    username = db.StringField(required=True)
    password = db.StringField(required=True)

    def to_json(self):
        return {
            "website": self.website,
            "username": self.username,
            "password": self.password,  # Consider using encryption and not sending this raw
        }


# Flask routes and logic
@app.route('/')
def home():
    return render_template('index.html', error_message='')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('login--username')
        password = request.form.get('login--password')
        user = NewUser.objects(username=username, password=password).first()

        if user:
            session['username'] = user.username
            return redirect('/dashboard')  # Assuming there's a dashboard route
        else:
            return render_template('login.html', error_message="Invalid username or password")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = NewUser(
            name=request.form.get('register--name'),
            email=request.form.get('register--email'),
            username=request.form.get('register--username'),
            password=request.form.get('register--password'),
        )
        try:
            user.save()
            return redirect('/login')
        except:
            return render_template("register.html", error_message="Username already exists or error in registration")

    return render_template('register.html')


@app.route('/gen_pass', methods=['GET'])
def generate_password():
    prompt = ("Generate a strong password with at least 16 characters, including a mix of uppercase letters, "
              "lowercase letters, digits, and special characters.")
    response = openai.Completion.create(
        engine="davinci",  # Updated model engine name
        prompt=prompt,
        max_tokens=16,
        temperature=0.5
    )
    password = response.choices[0].text.strip()
    return jsonify(password=password)


# Additional routes for handling passwords...

if __name__ == "__main__":
    app.run(debug=True)
