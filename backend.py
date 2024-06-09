import os
import json
from flask import Flask, redirect, request, session, url_for, render_template
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Path to your OAuth 2.0 Client ID JSON file
CLIENT_SECRETS_FILE = 'path/to/client_secret.json'

SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
API_SERVICE_NAME = 'docs'
API_VERSION = 'v1'

def get_credentials():
    if 'credentials' not in session:
        return None
    credentials = Credentials(**session['credentials'])
    return credentials

@app.route('/')
def index():
    credentials = get_credentials()
    if not credentials or not credentials.valid:
        return redirect('authorize')
    return render_template('index.html')

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('index'))

@app.route('/type', methods=['POST'])
def type_text():
    credentials = get_credentials()
    if not credentials:
        return redirect('authorize')
    
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    
    # Create a new document if one does not exist
    if 'document_id' not in session:
        title = 'New Document'
        body = {'title': title}
        doc = service.documents().create(body=body).execute()
        session['document_id'] = doc['documentId']
    
    document_id = session['document_id']
    text = request.form.get('text')
    requests = [{'insertText': {'location': {'index': 1}, 'text': text}}]
    
    result = service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
    return jsonify({'status': 'success', 'documentId': document_id})

def credentials_to_dict(credentials):
    return {'token': credentials.token, 'refresh_token': credentials.refresh_token, 'token_uri': credentials.token_uri, 'client_id': credentials.client_id, 'client_secret': credentials.client_secret, 'scopes': credentials.scopes}

if __name__ == '__main__':
    app.run(debug=True)
