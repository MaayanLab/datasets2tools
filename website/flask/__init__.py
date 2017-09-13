#################################################################
#################################################################
############### Datasets2Tools Website Backend ##################
#################################################################
#################################################################
##### Author: Denis Torre
##### Affiliation: Ma'ayan Laboratory,
##### Icahn School of Medicine at Mount Sinai

#################################################################
#################################################################
############### 1. App Configuration ############################
#################################################################
#################################################################

#############################################
########## 1. Load libraries
#############################################
##### 1. Flask modules #####
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError
from flask_dropzone import Dropzone
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker

##### 2. Python modules #####
import pandas as pd
import os, json, random, sys
from StringIO import StringIO

##### 3. Custom modules #####
sys.path.append('static/py')
from Datasets2Tools import Datasets2Tools

#############################################
########## 2. App Setup
#############################################
##### 1. Flask App #####
entry_point = '/datasets2tools'
app = Flask(__name__)
dropzone = Dropzone(app)

##### 2. Database connection #####
# Database Connection Data
dbFile = '../../db.txt'
if os.path.exists(dbFile):
	with open(dbFile) as openfile: os.environ['SQLALCHEMY_DATABASE_URI'], os.environ['SECRET_KEY'] = openfile.readlines()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DROPZONE_MAX_FILE_SIZE'] = 10

# Database App Connection
db = SQLAlchemy(app)
engine = db.engine
Session = sessionmaker(bind=engine)
metadata = MetaData()
metadata.reflect(bind=engine)
tables = metadata.tables

##### 3. Login manager #####
# Login manager definition
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Class
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(15), unique=True)
	email = db.Column(db.String(50), unique=True)
	password = db.Column(db.String(80))
	
#############################################
########## 3. General Setup
#############################################
##### 1. Variables #####
# Default options
default_search_options = {'object_type': 'canned_analysis', 'offset': 1, 'page_size': 10, 'sort_by': 'relevance'}

# Object identifiers
object_identifier_columns = {'dataset': 'dataset_accession', 'tool': 'tool_name', 'canned_analysis': 'canned_analysis_accession'}

##### 2. Datasets2Tools API #####
# Datasets2Tools API
Datasets2Tools = Datasets2Tools(engine, Session, tables)

#################################################################
#################################################################
############### 1. App Configuration ############################
#################################################################
#################################################################

#######################################################
#######################################################
########## 1. Login and Error Handling
#######################################################
#######################################################

#############################################
########## 1. Load User
#############################################

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

#############################################
########## 2. Login
#############################################

@app.route(entry_point+'/login', methods=['POST'])
def login():
	login_data = request.form.to_dict()
	user = User.query.filter_by(email=login_data['email']).first()
	if user:
		if check_password_hash(user.password, login_data['password']):
			login_user(user, remember=False)
			return redirect(url_for('index'))
		else:
			flash('Sorry, wrong username or password. Please try again.', 'login-error')
			return redirect(url_for('index', login="true"))
	else:
		flash('Sorry, wrong username or password. Please try again.', 'login-error')
		return redirect(url_for('index', login="true"))

#############################################
########## 3. Sign Up
#############################################

@app.route(entry_point+'/signup', methods=['POST'])
def signup():
	signup_data = request.form.to_dict()
	signup_data['password'] = generate_password_hash(signup_data['password'], method='sha256')
	new_user = User(username=signup_data['username'], email=signup_data['email'], password=signup_data['password'])
	try:
		db.session.add(new_user)
		db.session.commit()
		login_user(new_user, remember=False)
		return redirect(url_for('index'))
	except IntegrityError as e:
		db.session.rollback()
		duplicate_field = e.message.split("'")[-2].title()
		flash('{duplicate_field} already exists. Please try another.'.format(**locals()), 'signup-error')
		return redirect(url_for('index', signup="true"))

#############################################
########## 4. Log Out
#############################################

@app.route(entry_point+'/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

#############################################
########## 5. Not Found
#############################################

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

#######################################################
#######################################################
########## 2. Page Routes
#######################################################
#######################################################

#############################################
########## 1. Homepage
#############################################

@app.route(entry_point)
def index():
	return render_template('index.html')

#############################################
########## 2. Search Page
#############################################

@app.route(entry_point+'/search')
def search():

	# Get search dictionaries
	search_filters = request.args.to_dict()
	search_options = {x: search_filters.pop(x, default_search_options[x]) for x in default_search_options.keys()}

	# Search database
	search_data = Datasets2Tools.search(search_filters = search_filters, search_options = search_options)

	# Return template
	return render_template('search.html', object_type=search_options['object_type'], search_data=search_data)

#############################################
########## 3. Landing Pages
#############################################

@app.route(entry_point+'/landing/<object_type>/<object_identifier>')
def landing(object_type, object_identifier):

	# Get search dicts
	landing_search_filters = {object_identifier_columns[object_type]: object_identifier}
	landing_search_options = default_search_options.copy()
	landing_search_options.update({'object_type': object_type})

	# Get object data
	object_data = Datasets2Tools.search(search_filters = landing_search_filters, search_options = landing_search_options, get_related_objects=True, get_fairness=True, user_id=current_user.get_id()).search_results[0]

	# Get associated objects
	associated_objects = {}
	for associated_object_type in ['dataset', 'tool', 'canned_analysis']:
		if associated_object_type != object_type:
			associated_search_filters, associated_search_options = landing_search_filters.copy(), default_search_options.copy()
			associated_search_options.update({'object_type': associated_object_type})
			if request.args.get('object_type') == associated_object_type:
				parameters = request.args.to_dict()
				associated_search_options.update({x: parameters.pop(x, default_search_options[x]) for x in associated_search_options.keys()})
				associated_search_filters.update(parameters)
			associated_objects[associated_object_type] = Datasets2Tools.search(search_filters = associated_search_filters, search_options = associated_search_options, get_related_objects=False, get_fairness=False)
	# Return template
	return render_template('landing.html', object_data=object_data, object_type=object_type, associated_objects=associated_objects)

#############################################
########## 4. Contribute Page
#############################################

@app.route(entry_point+'/contribute')
def contribute():
	return render_template('contribute.html')

#######################################################
#######################################################
########## 3. APIs
#######################################################
#######################################################

#############################################
########## 1. FAIRness Submission
#############################################

@app.route(entry_point+'/api/upload/fairness_evaluation', methods=['POST'])
def upload_evaluation_api():

	# Upload
	if current_user.is_authenticated:
		Datasets2Tools.upload_evaluation(evaluation_scores = request.form.to_dict())

	# Return 
	return ''

#############################################
########## 2. Upload Analysis
#############################################

@app.route(entry_point+'/api/upload/analysis', methods=['POST'])
def upload_analysis_api():

	# Read file
	analysis_file = StringIO(request.files['file'].read())

	# Upload file
	Datasets2Tools.upload_analyses(analysis_file = analysis_file, user_id = current_user.get_id())

	# Return
	return 'upload_results'

#############################################
########## 3. Serve static files
#############################################

@app.route(entry_point+'/static/<path:path>')
def static_files(path):
	return send_from_directory('static', path)

#############################################
########## 4. Test Search
#############################################

@app.route(entry_point+'/testsearch')
def test_search():

	# Get request dict
	search_filters = request.args.to_dict()

	# Get non-search options
	search_options = {x: search_filters.pop(x, default_search_options[x]) for x in default_search_options.keys()}

	# Perform search
	results = Datasets2Tools.search(search_filters = search_filters, search_options = search_options, get_fairness=True, user_id=current_user.get_id())
	return json.dumps(results.search_results[0])

#############################################
########## 5. Regular Update
#############################################

@app.route(entry_point+'/api/update')
def update_api():
	if current_user.get_id() == '1':
		Datasets2Tools.update_database(os.getcwd().replace('/website/flask', '/updater/results'))
	return ''

#######################################################
#######################################################
########## 3. Run App
#######################################################
#######################################################

#############################################
########## 1. Run
#############################################
if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')