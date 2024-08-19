from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend
import matplotlib.pyplot as plt
from fpdf import FPDF
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Initialize the database
def init_db():
    with sqlite3.connect('tasks.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, task TEXT)')
        conn.commit()

init_db()

# User class for authentication
class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        if username == 'admin':
            user = User()
            user.id = username
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

# Route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route for displaying tasks
@app.route('/')
@login_required
def index():
    with sqlite3.connect('tasks.db') as conn:
        tasks = conn.execute('SELECT * FROM tasks').fetchall()
    return render_template('index.html', tasks=tasks)

# Route for adding tasks
@app.route('/add', methods=['POST'])
@login_required
def add():
    task = request.form.get('task')
    if task:
        with sqlite3.connect('tasks.db') as conn:
            conn.execute('INSERT INTO tasks (task) VALUES (?)', (task,))
            conn.commit()
    return redirect(url_for('index'))

# Route for deleting tasks
@app.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    with sqlite3.connect('tasks.db') as conn:
        conn.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        conn.commit()
    return redirect(url_for('index'))

# Route for plotting results
@app.route('/plot')
@login_required
def plot():
    with sqlite3.connect('tasks.db') as conn:
        df = pd.read_sql_query('SELECT * FROM tasks', conn)
    
    plt.figure(figsize=(10, 6))
    word_counts = df['task'].str.split(expand=True).stack().value_counts()
    word_counts.plot(kind='bar')
    plt.title('Task Word Frequency')
    plt.xlabel('Words')
    plt.ylabel('Frequency')
    
    plt.savefig('static/task_plot.png')  # Save the plot to the static directory

    # Pass word_counts to the template
    return render_template('plot.html', plot_url='static/task_plot.png', word_counts=word_counts)


@app.route('/analysis')
@login_required
def analysis():
    with sqlite3.connect('tasks.db') as conn:
        df = pd.read_sql_query('SELECT * FROM tasks', conn)
    
    task_count = df.shape[0]
    word_counts = df['task'].str.split(expand=True).stack().value_counts()
    
    return render_template('analysis.html', task_count=task_count, word_counts=word_counts)



# Route for generating reports
@app.route('/report')
@login_required
def report():
    with sqlite3.connect('tasks.db') as conn:
        df = pd.read_sql_query('SELECT * FROM tasks', conn)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Task Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Total Tasks: {df.shape[0]}", ln=True, align='L')
    
    pdf.output("task_report.pdf")
    
    return send_file("task_report.pdf", as_attachment=True)

# Route for help
@app.route('/help')
def help():
    return render_template('help.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=False)

