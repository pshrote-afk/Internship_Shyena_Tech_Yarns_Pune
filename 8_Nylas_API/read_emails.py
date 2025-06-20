from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Replace with your actual values
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
API_BASE = 'https://api.us.nylas.com'
NYLAS_API_KEY = os.getenv('NYLAS_API_KEY')


@app.route('/callback')
def callback():
    # Step 3: Handle callback and get authorization code
    auth_code = request.args.get('code')

    if not auth_code:
        return "Error: No authorization code received", 400

    # Step 4: Exchange code for grant
    token_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': auth_code
    }

    try:
        response = requests.post(
            f'{API_BASE}/v3/connect/token',
            json=token_data,
            headers={'Accept': 'application/json'}
        )

        result = response.json()

        if 'access_token' in result:
            # Save this grant_id for API calls
            grant_id = result.get('grant_id')
            access_token = result.get('access_token')

            return jsonify({
                'success': True,
                'grant_id': grant_id,
                'access_token': access_token
            })
        else:
            return jsonify({'error': result}), 400

    except Exception as e:
        return f"Error: {str(e)}", 500


def fetch_last_10_emails(grant_id):
    try:
        response = requests.get(
            f'{API_BASE}/v3/grants/{grant_id}/messages?limit=10&select=subject,from,date',
            headers={
                'Authorization': f'Bearer {NYLAS_API_KEY}',
                'Accept': 'application/json'
            }
        )

        data = response.json()
        print(data)
        return data
    except Exception as error:
        print(f'Error: {error}')
        return None


@app.route('/emails/<grant_id>')
def get_emails(grant_id):
    emails = fetch_last_10_emails(grant_id)
    if emails:
        return jsonify(emails)
    else:
        return "Error fetching emails", 500


if __name__ == '__main__':
    print("Starting server on http://localhost:5000")
    print("Callback URL: http://localhost:5000/callback")
    app.run(debug=True, port=5000)