from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # required for flash messages

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # change this
app.config['MYSQL_DB'] = 'interview_db'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    branches = [
        "Computer Engineering", "Information Technology", "Mechanical Engineering",
        "Civil Engineering", "Electronics & Telecommunication", "Electrical Engineering"
    ]

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        mobile = request.form['mobile']
        email = request.form['email']
        password = request.form['password']
        college=request.form['college']
        branch = request.form['branch']

        # Validate Mobile Number
        if not re.fullmatch(r'\d{10}', mobile):
            flash("Mobile number must be exactly 10 digits", "danger")
            return render_template('register.html', branches=branches)

        # Validate Email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address", "danger")
            return render_template('register.html', branches=branches)

        # Validate Password Strength
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$', password):
            flash("Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character", "danger")
            return render_template('register.html', branches=branches)

        # Insert into MySQL
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO users (name, address, mobile, email, password, college, branch)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, address, mobile, email, password, college, branch))
            mysql.connection.commit()
            flash("Registered Successfully!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Registration Failed: {e}", "danger")
        finally:
            cur.close()

    return render_template('register.html', branches=branches)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['email'] = user[4]  # assuming email is at index 4 in users table
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))

        else:
            flash("Invalid email or password", "danger")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/text-preparation')
def text_preparation():
    return render_template('company_list.html')

@app.route('/mic-preparation')
def mic_preparation():
    return render_template('company_list.html')

@app.route('/company/<company_name>')
def company_roles(company_name):
    cur = mysql.connection.cursor()
    cur.execute("SELECT role FROM company_roles WHERE company_name = %s", (company_name,))
    roles = cur.fetchall()
    cur.close()
    return render_template('roles.html', company_name=company_name, roles=roles)

from flask import session
from aimodule import evaluate_answers  # You'll implement this
import json

@app.route('/role-chat/<company_name>/<role_name>', methods=['GET', 'POST'])
def role_chat(company_name, role_name):
    if 'email' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    if 'questions' not in session:
        cur.execute("SELECT question FROM interview_questions WHERE company_name=%s AND role_name=%s",
                    (company_name, role_name))
        questions = [q[0] for q in cur.fetchall()]
        session['questions'] = questions
        session['current_q'] = 0

    questions = session['questions']
    current_q = session['current_q']

    if request.method == 'POST':
        user_answer = request.form['user_answer']
        if current_q > 0:
            question = questions[current_q - 1]
    # Save answer to DB

        email = session['email']

        # Store the answer
        cur.execute("""
            INSERT INTO user_answers (user_email, company_name, role_name, question, answer)
            VALUES (%s, %s, %s, %s, %s)
        """, (email, company_name, role_name, question, user_answer))
        mysql.connection.commit()

    # Show next question or evaluate
    if current_q < len(questions):
        question = questions[current_q]
        session['current_q'] += 1
        cur.close()
        return render_template('role_chat.html', company_name=company_name, role_name=role_name, question=question)
    else:
        # All questions answered: Evaluate
        cur.execute("""
            SELECT question, answer FROM user_answers 
            WHERE user_email = %s AND company_name = %s AND role_name = %s
        """, (session['email'], company_name, role_name))
        qa_pairs = cur.fetchall()
        cur.close()

        evaluation = evaluate_answers(qa_pairs)  # AI evaluation of all answers

        # Clear session and user answers (optional: archive first)
        session.pop('questions', None)
        session.pop('current_q', None)
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM user_answers WHERE user_email = %s AND company_name = %s AND role_name = %s",
                    (session['email'], company_name, role_name))
        mysql.connection.commit()
        cur.close()

        return render_template('evaluation.html', evaluation=evaluation)
if __name__ == '__main__':
    app.run(debug=True)