from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import secrets
from datetime import datetime
from sklearn.metrics import confusion_matrix
import numpy as np

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
db = SQLAlchemy(app)

# Database Models
class UserQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    response = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_admission_related = db.Column(db.Boolean, default=True)
    user_feedback = db.Column(db.String(50))

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Create tables
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        admin = Admin(username='admin', password='admin123')  # Change in production
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin'] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    queries = UserQuery.query.all()
    
    # Generate analytics
    feedback_counts = db.session.query(
        UserQuery.user_feedback,
        db.func.count(UserQuery.user_feedback)
    ).group_by(UserQuery.user_feedback).all()
    
    # Pie chart
    fig1, ax1 = plt.subplots()
    labels = [f[0] or 'No feedback' for f in feedback_counts]
    sizes = [f[1] for f in feedback_counts]
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%')
    ax1.axis('equal')
    pie_chart = plot_to_img(fig1)
    
    # Confusion matrix (simplified example)
    y_true = [True, True, False, True, False]
    y_pred = [True, False, False, True, True]
    cm = confusion_matrix(y_true, y_pred)
    fig2, ax2 = plt.subplots()
    ax2.matshow(cm, cmap=plt.cm.Blues)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax2.text(x=j, y=i, s=cm[i, j], va='center', ha='center')
    ax2.set_xlabel('Predicted')
    ax2.set_ylabel('Actual')
    confusion_img = plot_to_img(fig2)
    
    return render_template('dashboard.html', 
                         queries=queries,
                         pie_chart=pie_chart,
                         confusion_matrix=confusion_img)

def plot_to_img(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

if __name__ == '__main__':
    app.run(debug=True)