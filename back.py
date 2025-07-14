from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from markupsafe import Markup
from flask_cors import CORS
import os
import base64
import requests
import json
import datetime
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import logging
from bson import ObjectId
from functools import wraps
from flask_bcrypt import Bcrypt
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import certifi
from dotenv import load_dotenv
from google_sheets_integration import append_to_master_sheet

app = Flask(__name__)
# Secure Flask secret key from environment
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key_change_me')
CORS(app)
bcrypt = Bcrypt(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
# Gemini API key from environment
GEMINI_API_KEY = 'AIzaSyBZW-SFFPMB-zkWfYGbMGlo-pdOqzslw3M'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'

# MongoDB configuration
# MongoDB configuration
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'visiting_card'
COLLECTION_NAME = 'cards'

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MongoDB client (local, no certifi needed)
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
users_collection = db['users']

reset_tokens = {}

# SMTP configuration (replace with your real credentials)
SMTP_SERVER = 'smtp.example.com'  # e.g., 'smtp.gmail.com'
SMTP_PORT = 587  # e.g., 587 for TLS
SMTP_USERNAME = 'your_email@example.com'
SMTP_PASSWORD = 'your_email_password'
SENDER_EMAIL = 'your_email@example.com'

# Secure session cookies for production
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

load_dotenv()



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image_to_base64(image_path):
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_details_with_gemini(image_base64):
    """Extract details from image using Gemini API"""
    headers = {
        'Content-Type': 'application/json',
    }
    
    prompt = """
    Please analyze this visiting card image and extract the following information in JSON format:
    {
        "name": "Full name of the person",
        "company": "Company name",
        "designation": "Job title/position",
        "email": "Email address",
        "phone": "Phone number",
        "address": "Address",
        "website": "Website URL",
        "additional_info": "Any other relevant information"
    }
    
    If any field is not found, set it to null. Return only the JSON object, no additional text.
    """
    
    data = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_base64
                    }
                }
            ]
        }]
    }
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                # Try to extract JSON from the response
                try:
                    # Find JSON in the response
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = content[start_idx:end_idx]
                        return json.loads(json_str)
                    else:
                        return {"error": "No JSON found in response"}
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON response", "raw_response": content}
            else:
                return {"error": "No content in response"}
        else:
            print(f"Gemini API request failed: {response.status_code} {response.text}")
            return {"error": f"API request failed with status {response.status_code}", "details": response.text}
          
    except Exception as e:
        print(f"Gemini API request exception: {e}")
        return {"error": f"Request failed: {str(e)}"}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_user_by_email(email):
    return users_collection.find_one({'email': email})

def is_strong_password(password):
    # At least 8 chars, one upper, one lower, one digit, one special char
    if (len(password) < 8 or
        not re.search(r'[A-Z]', password) or
        not re.search(r'[a-z]', password) or
        not re.search(r'\d', password) or
        not re.search(r'[^A-Za-z0-9]', password)):
        return False
    return True

def get_user_by_employee_id(employee_id):
    return users_collection.find_one({'employee_id': employee_id})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['email']
        password = request.form['password']
        if '@' in login_input:
            user = get_user_by_email(login_input)
        else:
            user = get_user_by_employee_id(login_input)
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user'] = user['email']
            session['name'] = user.get('name', '')
            session['show_welcome_modal'] = True
            session.permanent = False  # Ensure session cookie is not persistent
            return redirect(url_for('index'))
        else:
            flash('Invalid email/employee ID or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return render_template('logout_redirect.html')

@app.route('/')
@login_required
def index():
    name = session.get('name', '')
    if name:
        name = name.capitalize()
    show_welcome_modal = session.pop('show_welcome_modal', False)
    if 'just_logged_in' in session:
        flash(f"Welcome, {name}!", "success")
        session.pop('just_logged_in')
    return render_template('index.html', name=name, show_welcome_modal=show_welcome_modal)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            print('No file part in request.files')
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            print('No selected file')
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Encode image to base64
            image_base64 = encode_image_to_base64(filepath)
            
            # Extract details using Gemini API
            extracted_data = extract_details_with_gemini(image_base64)
            
            if 'error' in extracted_data:
                print(f"Gemini extraction error: {extracted_data}")
                os.remove(filepath)
                return jsonify({'error': extracted_data['error'], 'details': extracted_data.get('details', '')}), 400
            
            # Add timestamp, filename, and scanned_by to the data
            extracted_data['uploaded_at'] = datetime.datetime.now()
            extracted_data['original_filename'] = filename
            extracted_data['scanned_by'] = session['user']
            extracted_data['shared'] = False

            # Stricter duplicate check (by normalized email, phone, or name+company)
            email = extracted_data.get('email', '').strip().lower()
            phone = extracted_data.get('phone', '').strip()
            name = extracted_data.get('name', '').strip().lower()
            company = extracted_data.get('company', '').strip().lower()

            duplicate_query = {'scanned_by': session['user']}
            or_conditions = []

            if email:
                or_conditions.append({'email': email})
            if phone:
                or_conditions.append({'phone': phone})
            if name and company:
                or_conditions.append({'name': name, 'company': company})

            if or_conditions:
                duplicate_query['$or'] = or_conditions
                duplicate = collection.find_one(duplicate_query)
                if duplicate:
                    os.remove(filepath)
                    return jsonify({'success': False, 'error': 'Duplicate card detected. This card already exists.'}), 409

            # Check for extract_only mode
            extract_only = request.args.get('extract_only') == '1'
            if extract_only:
                os.remove(filepath)
                return jsonify({'success': True, 'data': extracted_data, 'message': 'Card details extracted. Confirm to save.'})

            # Save to MongoDB
            result = collection.insert_one(extracted_data)
            extracted_data['_id'] = str(result.inserted_id)
            
            # Only export to Google Sheets for ashutosh.lab@c4i4.com
            user_email = session.get('user')
            print("Current user for Google Sheets export:", user_email)
            if user_email == 'ashutosh.lab@c4i4.com':
                try:
                    append_to_master_sheet(extracted_data)
                    print("Successfully exported to Google Sheets (master)")
                except Exception as e:
                    print(f"Failed to export to Google Sheets (master): {e}")
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'data': extracted_data,
                'message': 'Card details extracted and saved successfully!'
            })
        
        else:
            print('Invalid file type uploaded')
            return jsonify({'error': 'Invalid file type. Please upload JPG, JPEG, or PNG files.'}), 400
            
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/cards', methods=['GET'])
@login_required
def get_cards():
    """Get cards visible to the current user"""
    try:
        # Show cards shared by users or scanned by the default/common user
        query = {'$or': [
            {'scanned_by': 'c4i4.lab@c4i4.com'},
            {'shared': True}
        ]}
        cards = list(collection.find(query))
        # Extra safeguard: filter in Python as well
        cards = [card for card in cards if card.get('scanned_by') == 'c4i4.lab@c4i4.com' or card.get('shared') is True]
        for card in cards:
            card['_id'] = str(card['_id'])
        return jsonify({'success': True, 'cards': cards})
    except Exception as e:
        return jsonify({'error': f'Failed to fetch cards: {str(e)}'}), 500

@app.route('/update_card/<card_id>', methods=['PUT'])
def update_card(card_id):
    """Update card details in database"""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(card_id):
            return jsonify({'error': 'Invalid card ID'}), 400
        
        # Get update data from request
        update_data = request.get_json()
        
        # Remove any fields that shouldn't be updated
        fields_to_remove = ['_id', 'uploaded_at', 'original_filename']
        for field in fields_to_remove:
            update_data.pop(field, None)
        
        # Update the card in MongoDB
        result = collection.update_one(
            {'_id': ObjectId(card_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Card not found'}), 404
        
        if result.modified_count == 0:
            return jsonify({'error': 'No changes made'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Card updated successfully'
        })
        
    except Exception as e:
        print(f"Update card error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/delete_card/<card_id>', methods=['DELETE'])
def delete_card(card_id):
    """Delete card from database"""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(card_id):
            return jsonify({'error': 'Invalid card ID'}), 400
        
        # Delete the card from MongoDB
        result = collection.delete_one({'_id': ObjectId(card_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Card not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Card deleted successfully'
        })
        
    except Exception as e:
        print(f"Delete card error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        employee_id = request.form.get('employee_id', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate all fields
        if not all([name, employee_id, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('signup.html', name=name, employee_id=employee_id, email=email)

        # Passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html', name=name, employee_id=employee_id, email=email)

        # Password strength
        if not is_strong_password(password):
            flash('Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character.', 'danger')
            return render_template('signup.html', name=name, employee_id=employee_id, email=email)

        # Unique email
        if get_user_by_email(email):
            flash('Email already registered.', 'danger')
            return render_template('signup.html', name=name, employee_id=employee_id, email=email)

        # Unique employee ID
        if get_user_by_employee_id(employee_id):
            flash('Employee ID already registered.', 'danger')
            return render_template('signup.html', name=name, employee_id=employee_id, email=email)

        # Hash password and insert
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = {
            'name': name,
            'employee_id': employee_id,
            'email': email,
            'password': hashed_password
        }
        users_collection.insert_one(user)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

def send_reset_email(to_email, reset_link):
    subject = 'Password Reset Request'
    html_body = f"""
    <html>
    <body style='font-family: Arial, sans-serif; background: #f9f9f9; color: #222;'>
      <div style='max-width: 480px; margin: 40px auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 32px;'>
        <h2 style='color: #00bfae;'>Password Reset Request</h2>
        <p>Hello,</p>
        <p>You requested a password reset. Click the button below to reset your password:</p>
        <p style='text-align: center; margin: 32px 0;'>
          <a href='{reset_link}' target='_blank' style='display: inline-block; background: linear-gradient(90deg, #00ffc3 0%, #00d9a5 100%); color: #222; font-weight: 600; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-size: 1.1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.10);'>
            Reset Password
          </a>
        </p>
        <p>If you did not request this, please ignore this email.</p>
        <p style='color: #888; font-size: 0.95em;'>Thanks,<br>Visiting Card Reader Team</p>
      </div>
    </body>
    </html>
    """
    msg = MIMEMultipart('alternative')
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = get_user_by_email(email)
        if not user:
            flash('No account found with that email.', 'danger')
            return render_template('forgot_password.html')
        # Generate a secure token
        token = secrets.token_urlsafe(32)
        reset_tokens[email] = token
        # Send reset link via email
        reset_link = url_for('reset_password', token=token, _external=True)
        email_sent = send_reset_email(email, reset_link)
        if email_sent:
            flash('A password reset link has been sent to your email address.', 'success')
        else:
            flash('Failed to send reset email. Please try again later.', 'danger')
        return render_template('forgot_password.html')
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Find email by token
    email = None
    for k, v in reset_tokens.items():
        if v == token:
            email = k
            break
    if not email:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return render_template('reset_password.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html')
        if not is_strong_password(password):
            flash('Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character.', 'danger')
            return render_template('reset_password.html')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.update_one({'email': email}, {'$set': {'password': hashed_password}})
        reset_tokens.pop(email, None)
        return redirect(url_for('login', reset=1))
    return render_template('reset_password.html')

@app.route('/personal-cards')
@login_required
def personal_cards():
    user_email = session.get('user')
    # Backend safeguard: Only show cards if scanned_by matches the current user exactly
    if not user_email or user_email == 'c4i4.lab@c4i4.com':
        cards = []
    else:
        cards = list(collection.find({'scanned_by': user_email}))
        # Extra safeguard: filter in Python as well
        cards = [card for card in cards if card.get('scanned_by') == user_email]
        for card in cards:
            card['_id'] = str(card['_id'])
    if request.args.get('json') == '1':
        return jsonify({'success': True, 'cards': cards})
    return render_template('personal_cards.html', cards=cards)

@app.route('/share_card/<card_id>', methods=['POST'])
@login_required
def share_card(card_id):
    """Toggle the shared status of a personal card"""
    try:
        if not ObjectId.is_valid(card_id):
            return jsonify({'error': 'Invalid card ID'}), 400
        card = collection.find_one({'_id': ObjectId(card_id)})
        if not card:
            return jsonify({'error': 'Card not found'}), 404
        user_email = session.get('user')
        if card.get('scanned_by') != user_email:
            return jsonify({'error': 'Unauthorized'}), 403
        new_shared = not card.get('shared', False)
        collection.update_one({'_id': ObjectId(card_id)}, {'$set': {'shared': new_shared}})
        return jsonify({'success': True, 'shared': new_shared})
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
