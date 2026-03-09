from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import random
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timedelta
import json
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_secret_in_production"

# Load translations
def load_translations():
    try:
        with open('translations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"en": {}, "kn": {}}

TRANSLATIONS = load_translations()

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/disease_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT")),
            connection_timeout=10
        )
        return connection
    except Exception as e:
        print("DB ERROR:", e)
        return None
def init_db():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()

            password_hash = generate_password_hash("farmer123")
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE username = 'farmer'",
                (password_hash,)
            )

            admin_password_hash = generate_password_hash("admin123")
            cursor.execute(
                "UPDATE admin_users SET password_hash = %s WHERE username = 'admin'",
                (admin_password_hash,)
            )

            connection.commit()
            cursor.close()
            print("Database initialized successfully")

        except Error as e:
            print(f"Error initializing database: {e}")

        finally:
            connection.close()

# Helper functions
def is_logged_in():
    return session.get("username") is not None

def is_admin_logged_in():
    return session.get("admin_username") is not None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash("Please login to access this page", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_logged_in():
            flash("Admin access required", "danger")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT")),
            connection_timeout=10
        )
        return connection
    except Exception as e:
        print("DB ERROR:", e)
        return None

def get_current_admin():
    admin_username = session.get('admin_username')
    if not admin_username:
        return None
    connection = get_db_connection()
    if not connection:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users WHERE username = %s", (admin_username,))
        admin = cursor.fetchone()
        cursor.close()
        return admin
    except Error as e:
        print(f"Error fetching admin: {e}")
        return None
    finally:
        connection.close()

# Translation helper functions
def get_language():
    """Get current language preference from session, default to 'en'"""
    return session.get('language', 'en')

def set_language(lang):
    """Set language preference in session"""
    if lang in ['en', 'kn']:
        session['language'] = lang
    return lang

def t(key, default=""):
    """Translate a key to the current language"""
    lang = get_language()
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    elif 'en' in TRANSLATIONS and key in TRANSLATIONS['en']:
        return TRANSLATIONS['en'][key]
    return default

@app.before_request
def before_request():
    """Set language in template context"""
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=7)
    if 'language' not in session:
        session['language'] = 'en'

@app.context_processor
def inject_translation():
    """Make translation function and language available to all templates"""
    return {
        't': t,
        'get_language': get_language,
        'language': get_language()
    }

# Static data (keeping existing data structures)
TALUKA_DATA = {
    "Bengaluru Urban": ["Bengaluru North", "Bengaluru South", "Anekal", "Bangalore East"],
    "Mysuru": ["Mysuru", "Nanjangud", "T. Narsipur", "Hunsur", "Piriyapatna", "K.R. Nagar", "H.D. Kote"],
    "Mandya": ["Mandya", "Maddur", "Malavalli", "Pandavapura", "Srirangapatna", "Nagamangala", "K.R. Pet"],
    "Tumakuru": ["Tumakuru", "Gubbi", "Kunigal", "Tiptur", "Turuvekere", "Madhugiri", "Sira", "Pavagada", "Koratagere", "C.N. Halli"],
    "Hassan": ["Hassan", "Belur", "Alur", "Arkalgud", "Holenarasipura", "Channarayapatna", "Sakleshpur", "Arasikere"],
    "Chikkamagaluru": ["Chikkamagaluru", "Kadur", "Koppa", "Mudigere", "Narasimharajapura", "Sringeri", "Tarikere"],
    "Belagavi": ["Belagavi", "Bailhongal", "Gokak", "Hukkeri", "Khanapur", "Ramdurg", "Saundatti", "Parasgad", "Raybag", "Chikkodi"],
    "Dharwad": ["Dharwad", "Hubli", "Kalghatagi", "Kundgol", "Navalgund"],
    "Kalaburagi": ["Kalaburagi", "Afzalpur", "Aland", "Chincholi", "Chitapur", "Jewargi", "Sedam"],
    "Ballari": ["Ballari", "Hadagali", "Hagaribommanahalli", "Hoovina Hadagali", "Hospet", "Kudligi", "Sandur", "Siruguppa"]
}

SOIL_CROP_DATA = {
    "Bengaluru Urban": {
        "Bengaluru North": {
            "soilType": "Red Sandy Loam",
            "phLevel": "6.0 - 7.5",
            "kharifCrops": "Ragi, Maize, Groundnut, Sunflower",
            "rabiCrops": "Pulses (Bengal Gram), Vegetables, Flowers",
            "irrigation": "Drip irrigation recommended for efficient water use. Borewell and tank irrigation suitable.",
            "fertilizer": "NPK 19:19:19 for general use. Add organic manure (5 tons/acre). Micronutrients like Zinc for better yield."
        }
    }
}

SCHEMES = [
    {"name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)", "category": "Credit", "description": "Direct income support of ₹6,000 per year to all farmer families.", "eligibility": "All landholding farmer families", "benefits": "₹6,000 per year directly transferred to bank account", "howToApply": "Apply online at pmkisan.gov.in", "contact": "Toll-Free: 155261"}
]

INSURANCE_PLANS = [
    {
        "id": "basic",
        "name": "Basic Crop Protection",
        "icon": "🌱",
        "coverage": "₹50,000",
        "premium_per_acre": 500,
        "features": ["Natural calamity coverage", "Fire protection", "Theft coverage", "Basic pest damage"],
        "claim_process": "15 days",
        "coverage_period": "6 months"
    },
    {
        "id": "standard",
        "name": "Standard Farm Shield",
        "icon": "🛡️",
        "coverage": "₹1,50,000",
        "premium_per_acre": 1200,
        "features": ["All Basic features", "Weather-based coverage", "Disease protection", "Equipment coverage", "Free soil testing"],
        "claim_process": "10 days",
        "coverage_period": "1 year",
        "popular": True
    }
]

CROP_LIST = ["Tomato", "Potato", "Onion", "Cabbage", "Cauliflower", "Carrot", "Beans", "Brinjal", 
             "Ragi", "Paddy", "Maize", "Wheat", "Jowar", "Bajra",
             "Groundnut", "Soybean", "Cotton", "Sugarcane", "Banana", "Mango", "Coconut"]

# ==================== FARMER ROUTES ====================


# ==================== LANGUAGE ROUTES ====================

@app.route('/set-language/<lang>')
def set_lang(lang):
    """Set language preference"""
    set_language(lang)
    return redirect(request.referrer or url_for('landing'))

# ==================== FARMER ROUTES ====================

@app.route('/')
def landing():
    if is_admin_logged_in():
        return redirect(url_for('admin_dashboard'))
    if is_logged_in():
        return redirect(url_for('index'))
    return render_template('landing.html', language=get_language(), t=t)

@app.route('/home')
@login_required
def index():
    user = get_current_user()
    full_name = user.get('full_name', session.get('username')) if user else session.get('username')
    return render_template('index.html', logged_in=True, username=session.get('username'), 
                         full_name=full_name, user=user, show_marketplace_products=True, language=get_language(), t=t)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))
    if request.method == "GET":
        return render_template('login.html')
    
    data = request.form
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    connection = get_db_connection()
    if not connection:
        flash("Database connection error", "danger")
        return redirect(url_for('login'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        
        if not user or not check_password_hash(user['password_hash'], password):
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))
        
        session['username'] = username
        flash(f"Welcome back, {user.get('full_name', username)}!", "success")
        return redirect(url_for('index'))
    except Error as e:
        print(f"Login error: {e}")
        flash("An error occurred during login", "danger")
        return redirect(url_for('login'))
    finally:
        connection.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('index'))
    if request.method == "GET":
        return render_template('register.html')
    
    data = request.form
    username = data.get('username', '').strip()
    full_name = data.get('full_name', '').strip() or username
    password = data.get('password', '')
    password2 = data.get('password2', '')
    
    if not username or not password:
        flash("Please provide username and password", "danger")
        return redirect(url_for('register'))
    if password != password2:
        flash("Passwords do not match", "danger")
        return redirect(url_for('register'))
    
    connection = get_db_connection()
    if not connection:
        flash("Database connection error", "danger")
        return redirect(url_for('register'))
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username already taken", "danger")
            cursor.close()
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, full_name, password_hash, profile_completed) VALUES (%s, %s, %s, %s)",
            (username, full_name, password_hash, False)
        )
        connection.commit()
        cursor.close()
        flash("Registration successful! Please login", "success")
        return redirect(url_for('login'))
    except Error as e:
        print(f"Registration error: {e}")
        flash("An error occurred during registration", "danger")
        return redirect(url_for('register'))
    finally:
        connection.close()

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))

@app.route('/my-account', methods=['GET', 'POST'])
@login_required
def my_account():
    user = get_current_user()
    if not user:
        flash("User not found", "danger")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        connection = get_db_connection()
        if not connection:
            flash("Database connection error", "danger")
            return redirect(url_for('my_account'))
        try:
            data = request.form
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET full_name = %s, mobile = %s, aadhar = %s, dob = %s, 
                    location = %s, pincode = %s, land_size = %s, profile_completed = %s
                WHERE username = %s
            """, (
                data.get('full_name'), data.get('mobile'), data.get('aadhar'), data.get('dob'),
                data.get('location'), data.get('pincode'), data.get('land_size'), True,
                session.get('username')
            ))
            connection.commit()
            cursor.close()
            flash("Account updated successfully!", "success")
        except Error as e:
            print(f"Update error: {e}")
            flash("Error updating account", "danger")
        finally:
            connection.close()
        return redirect(url_for('my_account'))
    
    connection = get_db_connection()
    user_insurances = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM insurance_applications WHERE username = %s ORDER BY applied_date DESC", 
                         (session.get('username'),))
            user_insurances = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching insurances: {e}")
        finally:
            connection.close()
    
    return render_template('my_account.html', user=user, insurances=user_insurances)

# ==================== CROP APPLICATION WITH LIMITS ====================

@app.route('/crop-application')
@login_required
def crop_application():
    user = get_current_user()
    if not user or not user.get('profile_completed'):
        flash("Please complete your account information first", "warning")
        return redirect(url_for('my_account'))
    
    # Get crop limits from database
    connection = get_db_connection()
    crop_limits_list = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM crop_limits ORDER BY crop_name")
            crop_limits_list = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching crop limits: {e}")
        finally:
            connection.close()
    
    return render_template('crop_application_new.html', user=user, crops=CROP_LIST, crop_limits=crop_limits_list)

@app.route('/my-crop-applications')
@login_required
def my_crop_applications():
    user = get_current_user()
    connection = get_db_connection()
    applications = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM crop_applications WHERE username = %s ORDER BY created_at DESC",
                (session.get('username'),)
            )
            applications = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching applications: {e}")
        finally:
            connection.close()
    return render_template('my_crop_applications.html', user=user, applications=applications)

@app.route('/api/crop/check-limit', methods=['POST'])
@login_required
def check_crop_limit():
    data = request.json
    crop_name = data.get('crop_name')
    estimated_tonnes = float(data.get('estimated_tonnes', 0))
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "error": "Database error"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get crop limit info
        cursor.execute("SELECT * FROM crop_limits WHERE crop_name = %s", (crop_name,))
        limit_info = cursor.fetchone()
        
        if not limit_info:
            cursor.close()
            return jsonify({"success": False, "error": "Crop limit not found"}), 404
        
        current_applications = float(limit_info['current_applications_tonnes'])
        daily_limit = float(limit_info['daily_limit_tonnes'])
        remaining = daily_limit - current_applications
        
        # Get user's soil type for recommendations
        user = get_current_user()
        soil_type = "Red Sandy Loam"  # Default
        
        # Get alternative crops
        cursor.execute("SELECT recommended_crops FROM crop_soil_recommendations WHERE soil_type = %s", (soil_type,))
        soil_rec = cursor.fetchone()
        alternative_crops = soil_rec['recommended_crops'].split(', ') if soil_rec else []
        
        # Calculate adjusted price based on supply
        base_price = float(limit_info['base_price_per_kg'])
        supply_ratio = (current_applications + estimated_tonnes) / daily_limit
        
        if supply_ratio <= 0.7:
            adjusted_price = base_price * 1.1  # 10% bonus for under-supply
            price_trend = "HIGH"
        elif supply_ratio <= 0.9:
            adjusted_price = base_price
            price_trend = "NORMAL"
        elif supply_ratio <= 1.0:
            adjusted_price = base_price * 0.95
            price_trend = "MODERATE"
        else:
            adjusted_price = base_price * 0.8  # 20% reduction for over-supply
            price_trend = "LOW"
        
        cursor.close()
        
        return jsonify({
            "success": True,
            "crop_name": crop_name,
            "daily_limit": daily_limit,
            "current_applications": current_applications,
            "remaining": remaining,
            "estimated_tonnes": estimated_tonnes,
            "can_apply": (current_applications + estimated_tonnes) <= daily_limit,
            "status": limit_info['status'],
            "base_price": base_price,
            "adjusted_price": round(adjusted_price, 2),
            "price_trend": price_trend,
            "alternative_crops": alternative_crops[:5],
            "supply_percentage": round((current_applications / daily_limit) * 100, 1)
        })
        
    except Error as e:
        print(f"Error checking limit: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        connection.close()

@app.route('/api/crop/estimate-price', methods=['POST'])
@login_required
def estimate_crop_price():
    data = request.json
    crop_name = data.get('crop_name')
    estimated_tonnes = float(data.get('estimated_tonnes', 0))
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "error": "Database error"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crop_limits WHERE crop_name = %s", (crop_name,))
        limit_info = cursor.fetchone()
        cursor.close()
        
        if not limit_info:
            return jsonify({"success": False, "error": "Crop not found"}), 404
        
        base_price = float(limit_info['base_price_per_kg'])
        current_applications = float(limit_info['current_applications_tonnes'])
        daily_limit = float(limit_info['daily_limit_tonnes'])
        
        supply_ratio = (current_applications + estimated_tonnes) / daily_limit
        
        if supply_ratio <= 0.7:
            estimated_price = base_price * 1.1
            min_price = base_price * 1.05
            max_price = base_price * 1.15
        elif supply_ratio <= 0.9:
            estimated_price = base_price
            min_price = base_price * 0.95
            max_price = base_price * 1.05
        elif supply_ratio <= 1.0:
            estimated_price = base_price * 0.95
            min_price = base_price * 0.90
            max_price = base_price
        else:
            estimated_price = base_price * 0.8
            min_price = base_price * 0.75
            max_price = base_price * 0.85
        
        return jsonify({
            "success": True,
            "crop_name": crop_name,
            "estimated_price": round(estimated_price, 2),
            "min_price": round(min_price, 2),
            "max_price": round(max_price, 2),
            "supply_status": "High Demand" if supply_ratio < 0.7 else "Normal" if supply_ratio < 1.0 else "Oversupply"
        })
    except Error as e:
        print(f"Error estimating price: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        connection.close()

@app.route('/api/crop/apply', methods=['POST'])
@login_required
def apply_crop():
    user = get_current_user()
    data = request.json
    
    crop_name = data.get('crop_name')
    land_area = float(data.get('land_area'))
    expected_yield = float(data.get('expected_yield', 0))
    
    # Convert quintals to tonnes (1 quintal = 0.1 tonnes)
    estimated_tonnes = expected_yield * 0.1
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "error": "Database error"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Check if limit is exceeded
        cursor.execute("SELECT * FROM crop_limits WHERE crop_name = %s", (crop_name,))
        limit_info = cursor.fetchone()
        
        if not limit_info:
            cursor.close()
            return jsonify({"success": False, "error": "Crop not found"}), 404
        
        current_applications = float(limit_info['current_applications_tonnes'])
        daily_limit = float(limit_info['daily_limit_tonnes'])
        
        if limit_info['status'] == 'CLOSED':
            cursor.close()
            return jsonify({"success": False, "error": "Applications closed for this crop"}), 400
        
        if (current_applications + estimated_tonnes) > daily_limit:
            cursor.close()
            return jsonify({"success": False, "error": "Crop limit exceeded. Please choose alternative crop"}), 400
        
        # Calculate price at application
        base_price = float(limit_info['base_price_per_kg'])
        supply_ratio = (current_applications + estimated_tonnes) / daily_limit
        
        if supply_ratio <= 0.7:
            price_at_application = base_price * 1.1
        elif supply_ratio <= 0.9:
            price_at_application = base_price
        else:
            price_at_application = base_price * 0.95
        
        application_id = f"CRP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute("""
            INSERT INTO crop_applications 
            (application_id, user_id, username, farmer_name, mobile, location, 
             crop_name, crop_variety, land_area, expected_yield, estimated_quantity_tonnes,
             planting_date, expected_harvest_date, estimated_price_per_kg, price_at_application,
             status, limit_status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            application_id, user['id'], session.get('username'), user['full_name'],
            user['mobile'], user['location'], crop_name, data.get('crop_variety', ''),
            land_area, expected_yield, estimated_tonnes, data.get('planting_date'),
            data.get('expected_harvest_date'), data.get('estimated_price_per_kg'),
            price_at_application, 'Planned', 'Within Limit', data.get('notes', '')
        ))
        
        # Update crop limit
        cursor.execute("""
            UPDATE crop_limits 
            SET current_applications_tonnes = current_applications_tonnes + %s
            WHERE crop_name = %s
        """, (estimated_tonnes, crop_name))
        
        connection.commit()
        cursor.close()
        
        return jsonify({"success": True, "application_id": application_id})
    except Error as e:
        print(f"Error applying crop: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        connection.close()

# ==================== DISEASE REPORTING ====================

@app.route('/disease-report')
@login_required
def disease_report():
    user = get_current_user()
    return render_template('disease_report.html', user=user, crops=CROP_LIST)

@app.route('/my-disease-reports')
@login_required
def my_disease_reports():
    user = get_current_user()
    connection = get_db_connection()
    reports = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM disease_reports WHERE username = %s ORDER BY created_at DESC",
                (session.get('username'),)
            )
            reports = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching reports: {e}")
        finally:
            connection.close()
    return render_template('my_disease_reports.html', user=user, reports=reports)

@app.route('/api/disease/report', methods=['POST'])
@login_required
def submit_disease_report():
    user = get_current_user()
    
    # Handle file upload
    photo_path = None
    if 'disease_photo' in request.files:
        file = request.files['disease_photo']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            photo_path = f"uploads/disease_photos/{filename}"
    
    crop_name = request.form.get('crop_name')
    description = request.form.get('description', '')
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "error": "Database error"}), 500
    
    try:
        cursor = connection.cursor()
        report_id = f"DIS{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute("""
            INSERT INTO disease_reports 
            (report_id, user_id, username, farmer_name, mobile, crop_name, 
             location, disease_description, photo_path, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            report_id, user['id'], session.get('username'), user['full_name'],
            user.get('mobile'), crop_name, user.get('location'), description,
            photo_path, 'Pending'
        ))
        
        connection.commit()
        cursor.close()
        
        flash("Disease report submitted successfully! Admin will respond soon.", "success")
        return jsonify({"success": True, "report_id": report_id})
    except Error as e:
        print(f"Error submitting report: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        connection.close()

# ==================== INSURANCE ROUTES ====================

@app.route('/apply-insurance')
@login_required
def apply_insurance():
    user = get_current_user()
    if not user or not user.get('profile_completed'):
        flash("Please complete your account first", "warning")
        return redirect(url_for('my_account'))
    return render_template('apply_insurance_new.html', plans=INSURANCE_PLANS, user=user)

@app.route('/insurance-details')
@login_required
def insurance_details():
    user = get_current_user()
    connection = get_db_connection()
    user_insurances = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM insurance_applications WHERE username = %s ORDER BY applied_date DESC",
                         (session.get('username'),))
            user_insurances = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching insurances: {e}")
        finally:
            connection.close()
    return render_template('insurance_details.html', user=user, insurances=user_insurances)

@app.route('/api/insurance/apply', methods=['POST'])
@login_required
def apply_insurance_api():
    user = get_current_user()
    data = request.json
    
    if data.get('otp') != '123456':
        return jsonify({"success": False, "error": "Invalid OTP"}), 400
    
    application_id = f"INS{datetime.now().strftime('%Y%m%d%H%M%S')}"
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "error": "Database error"}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO insurance_applications 
            (application_id, user_id, username, farmer_name, aadhar, mobile, dob, 
             location, pincode, plan_id, plan_name, crop_type, land_size, premium, 
             coverage, status, validity_start, validity_end)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            application_id, user['id'], session.get('username'), user['full_name'],
            user['aadhar'], user['mobile'], user['dob'], user['location'], user['pincode'],
            data.get('plan_id'), data.get('plan_name'), data.get('crop_type'),
            data.get('land_size'), data.get('premium'), data.get('coverage'),
            'Pending Approval', datetime.now().strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        ))
        connection.commit()
        cursor.close()
        return jsonify({"success": True, "application_id": application_id})
    except Error as e:
        print(f"Error applying insurance: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        connection.close()

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if is_admin_logged_in():
        return redirect(url_for('admin_dashboard'))
    if request.method == "GET":
        return render_template('admin_login.html')
    
    data = request.form
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    connection = get_db_connection()
    if not connection:
        flash("Database connection error", "danger")
        return redirect(url_for('admin_login'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users WHERE username = %s", (username,))
        admin = cursor.fetchone()
        cursor.close()
        
        if not admin or not check_password_hash(admin['password_hash'], password):
            flash("Invalid admin credentials", "danger")
            return redirect(url_for('admin_login'))
        
        session['admin_username'] = username
        flash(f"Welcome Admin!", "success")
        return redirect(url_for('admin_dashboard'))
    except Error as e:
        print(f"Admin login error: {e}")
        flash("Error during login", "danger")
        return redirect(url_for('admin_login'))
    finally:
        connection.close()

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_username', None)
    flash("Admin logged out", "info")
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    admin = get_current_admin()
    connection = get_db_connection()
    stats = {
        'total_users': 0,
        'total_applications': 0,
        'total_insurances': 0,
        'pending_insurances': 0,
        'pending_disease_reports': 0
    }
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM users")
            stats['total_users'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM crop_applications")
            stats['total_applications'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM insurance_applications")
            stats['total_insurances'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM insurance_applications WHERE status = 'Pending Approval'")
            stats['pending_insurances'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM disease_reports WHERE status = 'Pending'")
            stats['pending_disease_reports'] = cursor.fetchone()['count']
            cursor.close()
        except Error as e:
            print(f"Error fetching stats: {e}")
        finally:
            connection.close()
    
    return render_template('admin_dashboard_new.html', admin=admin, stats=stats)

@app.route('/admin/crop-limits')
@admin_required
def admin_crop_limits():
    admin = get_current_admin()
    connection = get_db_connection()
    crop_limits = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM crop_limits ORDER BY crop_name")
            crop_limits = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching crop limits: {e}")
        finally:
            connection.close()
    
    return render_template('admin_crop_limits.html', admin=admin, crop_limits=crop_limits)

@app.route('/admin/crop-limit/<int:limit_id>/update', methods=['POST'])
@admin_required
def admin_update_crop_limit(limit_id):
    data = request.form
    connection = get_db_connection()
    
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE crop_limits 
                SET daily_limit_tonnes = %s, base_price_per_kg = %s, status = %s
                WHERE id = %s
            """, (
                data.get('daily_limit'),
                data.get('base_price'),
                data.get('status'),
                limit_id
            ))
            connection.commit()
            cursor.close()
            flash("Crop limit updated successfully", "success")
        except Error as e:
            print(f"Error updating limit: {e}")
            flash("Error updating limit", "danger")
        finally:
            connection.close()
    
    return redirect(url_for('admin_crop_limits'))

@app.route('/admin/crop-limit/reset', methods=['POST'])
@admin_required
def admin_reset_crop_limits():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE crop_limits SET current_applications_tonnes = 0, last_reset_date = CURDATE()")
            connection.commit()
            cursor.close()
            flash("All crop limits reset successfully", "success")
        except Error as e:
            print(f"Error resetting limits: {e}")
            flash("Error resetting limits", "danger")
        finally:
            connection.close()
    return redirect(url_for('admin_crop_limits'))

@app.route('/admin/disease-reports')
@admin_required
def admin_disease_reports():
    admin = get_current_admin()
    connection = get_db_connection()
    reports = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM disease_reports ORDER BY created_at DESC")
            reports = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching reports: {e}")
        finally:
            connection.close()
    
    return render_template('admin_disease_reports.html', admin=admin, reports=reports)

@app.route('/admin/disease-report/<int:report_id>', methods=['GET', 'POST'])
@admin_required
def admin_disease_report_detail(report_id):
    admin = get_current_admin()
    
    if request.method == 'POST':
        data = request.form
        connection = get_db_connection()
        
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""
                    UPDATE disease_reports 
                    SET admin_response = %s, recommended_medicine = %s, status = 'Responded',
                        responded_by = %s, responded_at = NOW()
                    WHERE id = %s
                """, (
                    data.get('response'),
                    data.get('medicine'),
                    session.get('admin_username'),
                    report_id
                ))
                connection.commit()
                cursor.close()
                flash("Response sent successfully", "success")
            except Error as e:
                print(f"Error responding: {e}")
                flash("Error sending response", "danger")
            finally:
                connection.close()
        
        return redirect(url_for('admin_disease_reports'))
    
    # GET request
    connection = get_db_connection()
    report = None
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM disease_reports WHERE id = %s", (report_id,))
            report = cursor.fetchone()
            cursor.close()
        except Error as e:
            print(f"Error fetching report: {e}")
        finally:
            connection.close()
    
    if not report:
        flash("Report not found", "danger")
        return redirect(url_for('admin_disease_reports'))
    
    return render_template('admin_disease_detail.html', admin=admin, report=report)

@app.route('/admin/users')
@admin_required
def admin_users():
    admin = get_current_admin()
    connection = get_db_connection()
    users = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching users: {e}")
        finally:
            connection.close()
    return render_template('admin_users.html', admin=admin, users=users)

@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    admin = get_current_admin()
    connection = get_db_connection()
    user = None
    crop_apps = []
    insurances = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                cursor.execute("SELECT * FROM crop_applications WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
                crop_apps = cursor.fetchall()
                cursor.execute("SELECT * FROM insurance_applications WHERE user_id = %s ORDER BY applied_date DESC", (user_id,))
                insurances = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching user: {e}")
        finally:
            connection.close()
    
    if not user:
        flash("User not found", "danger")
        return redirect(url_for('admin_users'))
    
    return render_template('admin_user_detail.html', admin=admin, user=user, crop_apps=crop_apps, insurances=insurances)

@app.route('/admin/crop-applications')
@admin_required
def admin_crop_applications():
    admin = get_current_admin()
    connection = get_db_connection()
    applications = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT ca.*, u.full_name, u.mobile, u.location 
                FROM crop_applications ca
                JOIN users u ON ca.user_id = u.id
                ORDER BY ca.created_at DESC
            """)
            applications = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching applications: {e}")
        finally:
            connection.close()
    
    return render_template('admin_crop_applications.html', admin=admin, applications=applications)

@app.route('/admin/insurances')
@admin_required
def admin_insurances():
    admin = get_current_admin()
    connection = get_db_connection()
    insurances = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM insurance_applications ORDER BY applied_date DESC")
            insurances = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"Error fetching insurances: {e}")
        finally:
            connection.close()
    
    return render_template('admin_insurances.html', admin=admin, insurances=insurances)

@app.route('/admin/insurance/<int:insurance_id>/update-status', methods=['POST'])
@admin_required
def admin_update_insurance_status(insurance_id):
    data = request.form
    new_status = data.get('status')
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE insurance_applications SET status = %s WHERE id = %s", (new_status, insurance_id))
            connection.commit()
            cursor.close()
            flash(f"Insurance status updated to {new_status}", "success")
        except Error as e:
            print(f"Error updating status: {e}")
            flash("Error updating status", "danger")
        finally:
            connection.close()
    
    return redirect(url_for('admin_insurances'))

# ==================== API ENDPOINTS ====================

@app.route('/api/talukas/<district>')
@login_required
def get_talukas(district):
    talukas = TALUKA_DATA.get(district, [])
    return jsonify(talukas)

@app.route('/api/soil-crop/<district>/<taluka>')
@login_required
def get_soil_crop_data(district, taluka):
    data = SOIL_CROP_DATA.get(district, {}).get(taluka)
    if data:
        return jsonify(data)
    return jsonify({"error": "Data not found"}), 404

@app.route('/api/weather/<location>')
@login_required
def get_weather(location):
    conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain']
    icons = {'Sunny': '☀️', 'Partly Cloudy': '⛅', 'Cloudy': '☁️', 'Light Rain': '🌧️'}
    condition = random.choice(conditions)
    return jsonify({
        "location": location,
        "temp": random.randint(25, 35),
        "condition": condition,
        "icon": icons[condition],
        "humidity": random.randint(50, 80),
        "windSpeed": random.randint(5, 20),
        "rainfall": random.randint(0, 10)
    })

@app.route('/api/weather/forecast')
@login_required
def get_forecast():
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    icons = ['☀️', '⛅', '☁️', '🌧️']
    return jsonify([{"day": day, "temp": random.randint(24, 32), "icon": random.choice(icons)} for day in days])

@app.route('/api/weather/extended')
@login_required
def get_extended_forecast():
    months = ['Current Month', 'Next Month', 'Month After']
    forecast = []
    for month in months:
        temp_avg = random.randint(24, 32)
        forecast.append({
            "month": month,
            "temp_avg": temp_avg,
            "temp_min": temp_avg - 5,
            "temp_max": temp_avg + 5,
            "rainfall": random.randint(50, 200),
            "humidity": random.randint(60, 85),
            "condition": random.choice(['Mostly Sunny', 'Partly Cloudy', 'Rainy'])
        })
    return jsonify(forecast)

@app.route('/api/advisory')
@login_required
def get_advisory():
    advisories = [
        "Good weather for irrigation.",
        "Suitable conditions for pesticides.",
        "Monitor for pest activity."
    ]
    return jsonify({"advisory": random.choice(advisories)})

@app.route('/api/products')
@login_required
def get_products():
    connection = get_db_connection()
    if not connection:
        return jsonify([])
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
        products = cursor.fetchall()
        cursor.close()
        return jsonify(products)
    except Error as e:
        print(f"Error fetching products: {e}")
        return jsonify([])
    finally:
        connection.close()

@app.route('/api/products/filter')
@login_required
def filter_products_api():
    return get_products()

@app.route('/api/products/add', methods=['POST'])
@login_required
def add_product():
    data = request.json
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "error": "Database error"}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO products (name, category, quantity, price, seller, location, contact, icon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('name'), data.get('category'), data.get('quantity'),
            data.get('price'), data.get('seller'), data.get('location'),
            data.get('contact'), '🌾'
        ))
        connection.commit()
        cursor.close()
        return jsonify({"success": True})
    except Error as e:
        print(f"Error adding product: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        connection.close()

@app.route('/api/schemes')
@login_required
def get_schemes():
    return jsonify(SCHEMES)

@app.route('/api/schemes/filter')
@login_required
def filter_schemes():
    return jsonify(SCHEMES)

@app.route('/api/admin/crop-stats')
@admin_required
def get_crop_stats():
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "error": "Database error"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT crop_name, daily_limit_tonnes, current_applications_tonnes, 
                   base_price_per_kg, status
            FROM crop_limits 
            ORDER BY crop_name
        """)
        stats = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "data": stats})
    except Error as e:
        print(f"Error fetching crop stats: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        connection.close()
if __name__ == '__main__':
    init_db()