
import os
import pandas as pd
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.utils import secure_filename
import uuid
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(filepath)

        session['uploaded_file_path'] = filepath
        return redirect('/visualize')

    return "Invalid file", 400

@app.route('/visualize')
def visualize():
    if 'uploaded_file_path' not in session:
        return "No file uploaded", 400

    file_path = session['uploaded_file_path']
    df = pd.read_csv(file_path)

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if len(numeric_cols) < 2:
        return "Not enough numeric columns for visualization", 400

    x_label, y_label = numeric_cols[0], numeric_cols[1]

    chart_data = df[[x_label, y_label]].dropna().head(10)

    return render_template('visualize.html',
        head=df.head().to_string(),
        describe=df.describe().to_string(),
        groupby=df.groupby(x_label)[y_label].mean().to_string(),
        labels=chart_data[x_label].astype(str).tolist(),
        values=chart_data[y_label].tolist(),
        x_label=x_label,
        y_label=y_label
    )

@app.route('/clear_session', methods=['POST'])
def clear_session():
    filepath = session.pop('uploaded_file_path', None)
    if filepath and os.path.exists(filepath):
        os.remove(filepath)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
