import os
import openai

from flask import Flask, render_template, request, session, redirect, jsonify
from flask_mongoengine import MongoEngine
from flask_session import Session

app = Flask(__name__, static_folder='static')

# Flask app configuration
app.config["SECRET_KEY"] = "oZ6fLot8TxPQeq45ZRyHx4mNFNLfd260aSXnbNANxH7uaroQlT7ir8HbuUgJ6dyn"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['MONGODB_SETTINGS'] = {
    'db': 'admin',
    'host': os.getenv('MONGODB_URI', 'mongodb+srv://arionnadotson78:Ztv4GSZLluQmBhLQ@cluster2.bueapka.mongodb.net/')
}
Session(app)

# Initialize MongoEngine with Flask app
db = MongoEngine(app)

# API key
openai.api_key = ('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')


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
            "password": self.password,
        }


# Flask routes and logic
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html', error_message='')


@app.route('/login', methods=['POST', 'GET'])
def login_user():
    try:
        user = NewUser.objects(
            username=request.form['login--username'], password=request.form['login--password']).first()
        if not user:
            return render_template('login.html', error_message="Invalid username or password")

        # Create Session
        session['username'] = request.form['login--username']
        # Get name from db
        name = NewUser \
            .objects(username=session['username']) \
            .get() \
            .to_json()['name']
        # Redirect to Dashboard
        return render_template('main.html', user=name, username=session['username'])
    except:
        return redirect('/')


@app.route('/register')
def register():
    return render_template('register.html', error_message='')


@app.route('/register', methods=['POST'])
def register_user():
    user = NewUser.objects(username=request.form['register--username']).first()
    if user:
        return render_template("register.html", error_message="Username already exists")
    else:
        new_user = NewUser(
            name=request.form['register--name'],
            email=request.form['register--email'],
            username=request.form['register--username'],
            password=request.form['register--password'],
        )
        new_user.save()
        return render_template('login.html')


@app.route('/gen_pass', methods=['GET'])
def generate_password():
    prompt = {
        "messages": [
            {"role": "system", "content": "You are a password expert."},
            {"role": "user", "content": "Generate a strong password with at least 16 characters, including a mix of "
                                        "uppercase letters, lowercase letters, digits, and special characters."
                                        "Give just the password, nothing else"}
        ]
    }
    # AI Generated
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",  # Correct model identifier
        messages=prompt['messages'],
        max_tokens=16,
        temperature=0.5
    )
    # AI Generated
    # Extracting the password from the response
    password = response['choices'][0]['message']['content'].strip()
    return jsonify(password=password)


@app.route('/save_pass', methods=['POST'])
def save_password():
    data = request.get_json()
    if 'user' not in data or 'website' not in data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing data"}), 400

    try:
        user = NewUser.objects(username=data['user']).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        new_password = Passwords(
            user=user,
            website=data['website'],
            username=data['username'],
            password=data['password']
        )
        new_password.save()
        return jsonify({"message": "Saved"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_pass', methods=['GET'])
def get_password():
    if 'username' not in session:
        return redirect('/')

    # Retrieve the user document first.
    user = NewUser.objects(username=session['username']).first()
    if not user:
        # Error Handling
        return jsonify({"error": "User not found"}), 404

    # Use the user object to filter the Passwords.
    passwords = Passwords.objects(user=user)
    data = [password.to_json() for password in passwords]
    return jsonify({"passwords": data}), 200


@app.route('/search_pass', methods=['POST'])
def search_password():
    data = request.get_json()
    if not data or 'website' not in data:
        return jsonify({"error": "Missing website parameter"}), 400

    try:
        user = NewUser.objects(username=session['username']).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        passwords = Passwords.objects(user=user, website__icontains=data['website'])
        return jsonify({"passwords": [pw.to_json() for pw in passwords]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/del_pass', methods=['POST'])
def delete_password():
    data = request.get_json()
    if not data or 'website' not in data or 'username' not in data:
        return jsonify({"error": "Missing necessary fields"}), 400

    try:
        user = NewUser.objects(username=session['username']).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        password_record = Passwords.objects(
            user=user,
            website=data['website'],
            username=data['username']
        ).first()

        if password_record:
            password_record.delete()
            return jsonify({"message": "Password deleted successfully"}), 200
        else:
            return jsonify({"error": "Password not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/logout')
def logout():
    session['username'] = None
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
