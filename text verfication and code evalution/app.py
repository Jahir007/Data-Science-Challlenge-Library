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
        new_problem = Problem(problem=problem, solution="")
        db.session.add(new_problem)
        db.session.commit()
        return redirect(url_for('index'))

    problems = Problem.query.all()
    return render_template('index.html', problems=problems)

@app.route('/submit_solution', methods=['POST'])
def submit_solution():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    problem_id = request.form['problem_id']
    solution = request.form['solution']

    problem = Problem.query.get(problem_id)
    if problem:
        problem.solution = solution
        db.session.commit()

    return redirect(url_for('problems_list'))

@app.route('/problems_list')
def problems_list():
    problems = Problem.query.all()
    return render_template('problems_list.html', problems=problems)

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

@app.route('/problem_submission', methods=['GET', 'POST'])
def problem_submission():
    if request.method == 'POST':
        problem = request.form['problem']
        new_problem = Problem(problem=problem, solution="")
        db.session.add(new_problem)
        db.session.commit()
        return redirect(url_for('problem_submission'))

    problems = Problem.query.all()
    return render_template('problem_submission.html', problems=problems)

@app.route('/code_evaluation', methods=['GET', 'POST'])
def code_evaluation():
    if request.method == 'POST':
        problems = Problem.query.all()
        return render_template('code_evaluation.html', problems=problems)

    return redirect(url_for('problem_submission'))

@app.route('/evaluate_code', methods=['POST'])
def evaluate_code():
    problem = request.form['problem']
    user = request.form['user']
    user_code = request.form['code']
    problem_obj = Problem.query.filter_by(problem=problem).first()

    # Check if the problem exists
    if not problem_obj:
        return redirect(url_for('code_evaluation', error_message="Problem not found. Please select a valid problem."))

    # Evaluate the user's code
    try:
        # Prepare a dictionary for capturing the user's code output
        output_dict = {}
        exec(user_code, output_dict)
        user_output = output_dict.get('output', '')

        # Compare the user's output with the expected solution
        if user_output == problem_obj.solution:
            score = 100.0
            error_message = None
        else:
            score = 0.0
            error_message = "Output does not match the expected solution."
    except Exception as e:
        score = 0.0
        error_message = str(e)
        user_output = ''

    # Save the attempt in the database
    new_attempt = Attempt(user=user, problem_id=problem_obj.id, attempt=user_code, score=score)
    db.session.add(new_attempt)
    db.session.commit()

    # Redirect to the code evaluation page with the result
    return redirect(url_for('code_evaluation', score=score, user_output=user_output,
                            solution_output=problem_obj.solution, error_message=error_message, problem=problem_obj.problem))

if __name__ == '__main__':
    app.run(debug=True)
