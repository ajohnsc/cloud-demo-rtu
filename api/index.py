import os
import json
from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- Firebase Initialization ---
# The service account JSON is loaded from the Vercel environment variable.
# On Vercel, define 'FIREBASE_CREDENTIALS_JSON' as an Environment Variable
# containing the JSON string of your Firebase Service Account Key.
try:
    cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if cred_json:
        # Load the JSON string from the environment variable
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase successfully initialized.")
    else:
        # This will run if the environment variable is not set (e.g., during basic local testing)
        print("Error: FIREBASE_CREDENTIALS_JSON environment variable not found. Database access will fail.")
        db = None
except Exception as e:
    print(f"Firebase initialization failed: {e}. Database functions are disabled.")
    db = None

app = Flask(__name__, template_folder='../templates')

COLLECTION_NAME = 'vercel_flask_todos'

@app.route('/', methods=['GET', 'POST'])
def index():
    if db is None:
        # Render a simple error page if DB failed to initialize
        return render_template('index.html', todos=[], db_error="Database not connected. Check Vercel environment variables.")

    if request.method == 'POST':
        task_content = request.form.get('content')
        if task_content:
            try:
                # Add a new document to the collection
                db.collection(COLLECTION_NAME).add({
                    'content': task_content,
                    'done': False,
                    'created_at': firestore.SERVER_TIMESTAMP
                })
            except Exception as e:
                print(f"Error adding document: {e}")
        return redirect(url_for('index'))

    # Fetch all todos, sorted by creation time
    try:
        todo_ref = db.collection(COLLECTION_NAME).order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        todos = []
        for doc in todo_ref:
            todo_data = doc.to_dict()
            # We need the document ID for deletion
            todos.append({
                'id': doc.id,
                'content': todo_data.get('content'),
                'done': todo_data.get('done', False)
            })
    except Exception as e:
        print(f"Error fetching documents: {e}")
        todos = []

    return render_template('index.html', todos=todos, db_error=None)

@app.post('/delete/<id>')
def delete(id):
    if db is None:
        return redirect(url_for('index')) # Cannot delete without DB

    try:
        # Delete the document by its ID
        db.collection(COLLECTION_NAME).document(id).delete()
    except Exception as e:
        print(f"Error deleting document: {e}")

    return redirect(url_for('index'))

if __name__ == '__main__':
    # This block is for local testing only
    # You must set the FIREBASE_CREDENTIALS_JSON environment variable locally
    # e.g., export FIREBASE_CREDENTIALS_JSON='{...your json content...}'
    app.run(debug=True)
