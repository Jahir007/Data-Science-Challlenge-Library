from flask import Flask, request, render_template, jsonify
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import traceback

app = Flask(__name__)

def gold_standard():
    data = load_iris()
    X = data.data
    y = data.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    return accuracy_score(y_test, predictions)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        student_code = request.form['code']
        global_vars = {}  # a dictionary for storing global variables from student code
        local_vars = {}  # a dictionary for storing local variables from student code

        try:
            exec(student_code, global_vars, local_vars)

            # Assume that student's prediction array is named `student_predictions`
            # and the test labels array is named `student_y_test`
            student_predictions = local_vars['student_predictions']
            student_y_test = local_vars['student_y_test']
            
            student_accuracy = accuracy_score(student_y_test, student_predictions)
            return render_template('index.html', accuracy=student_accuracy)
        except Exception as e:
            traceback_str = traceback.format_exc()
            return render_template('index.html', error=str(e), traceback=traceback_str)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)