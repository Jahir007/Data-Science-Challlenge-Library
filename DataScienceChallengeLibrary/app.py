from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem = db.Column(db.String(200), nullable=False)
    solution = db.Column(db.String(200), nullable=False)

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    attempt = db.Column(db.String(200), nullable=False)
    score = db.Column(db.Float, nullable=False)

def get_similarity(text1, text2):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)
    return similarity_matrix[0, 1]

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        # You can add your authentication logic here.
        # For simplicity, let's assume any user ID and password combination is valid.
        session['user_id'] = user_id
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/data_science_quiz')
def data_science_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('index'))

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        problem = request.form['problem']
        solution = request.form['solution']
        new_problem = Problem(problem=problem, solution=solution)
        db.session.add(new_problem)
        db.session.commit()
        return redirect(url_for('index'))

    problems = Problem.query.all()
    return render_template('index.html', problems=problems)

@app.route('/attempt/<problem_id>', methods=['GET', 'POST'])
def attempt(problem_id):
    problem = Problem.query.get(problem_id)
    if request.method == 'POST':
        user = request.form['user']
        attempt = request.form['attempt']
        score = get_similarity(attempt, problem.solution)
        new_attempt = Attempt(user=user, problem_id=problem_id, attempt=attempt, score=score)
        db.session.add(new_attempt)
        db.session.commit()
        return redirect(url_for('attempt', problem_id=problem_id))
    
    attempts = Attempt.query.filter_by(problem_id=problem_id).order_by(Attempt.score.desc())
    next_problem_id = Problem.query.filter(Problem.id > problem_id).order_by(Problem.id.asc()).first()
    if next_problem_id:
        next_problem_id = next_problem_id.id

    return render_template('attempt.html', problem=problem, attempts=attempts, next_problem_id=next_problem_id)

@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
