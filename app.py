from flask import (
    Flask, render_template, request, redirect, url_for, flash, session
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from datetime import datetime

# --- App setup ---
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.String(300))
    date_to_complete = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if current_user.is_authenticated:
        # Fetch all todos for the current user
        todos = Todo.query.filter_by(user_id=current_user.id).all()
        return render_template("index.html", todos=todos)
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("User already exists!", "danger")
            return redirect(url_for("register"))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/todo", methods=["GET", "POST"])
@login_required
def todo():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        date_to_complete = request.form["date_to_complete"]

        new_todo = Todo(
            title=title,
            description=description,
            date_to_complete=date_to_complete,
            user_id=current_user.id
        )
        db.session.add(new_todo)
        db.session.commit()
        flash("Task added successfully!", "success")
        return redirect(url_for("todo"))

    search_query = request.args.get("search", "")
    todos = Todo.query.filter(
        Todo.user_id == current_user.id,
        Todo.title.ilike(f"%{search_query}%")
    ).all()

    return render_template("todo.html", todos=todos, search_query=search_query)


@app.route("/delete/<int:todo_id>")
@login_required
def delete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    if todo.user_id != current_user.id:
        flash("You are not authorized to delete this task.", "danger")
        return redirect(url_for("index"))

    db.session.delete(todo)
    db.session.commit()
    flash("Task deleted successfully!", "info")
    return redirect(url_for("todo"))


# --- Run App ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
