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

# Other variables
fairness = [{"fairness_question": "The tool is hosted in one or more well-used repositories, if relevant repositories exist.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Source code is shared on a public repository.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Code is written in an open-source, free programming language.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "The tool inputs standard data format(s) consistent with community practice.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "All previous versions of the tool are made available.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Web-based version is available (in addition to desktop version).", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Source code is documented.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Pipelines that use the tool have been standardized and provide detailed usage guidelines.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "A tutorial page is provided for the tool.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Example datasets are provided.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Licensing information is provided on the tool's landing page.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Information is provided describing how to cite the tool.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Version information is provided for the tool.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "A paper about the tool has been published.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Video tutorials for the tool are available.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Contact information is provided for the originator(s) of the tool.", "fairness_score": random.uniform(-1, 1)}]

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

	# Get request dict
	search_filters = request.args.to_dict()

	# Get non-search options
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

	# Get display options
	display_options = {'offset': request.args.get('offset', default=1, type=int), 'page_size': request.args.get('page_size', default=10, type=int), 'sort_by': request.args.get('sort_by', default='relevance', type=str)}

	# Get search query
	search_options = {key:value for key, value in request.args.to_dict().iteritems() if key not in display_options.keys()}
	search_options[object_identifier_columns[object_type]] = object_identifier

	# Get selected object type
	selected_object_type = search_options.pop('object_type') if 'object_type' in search_options.keys() else None

	# Get selected object type filters
	associated_object_data = {x: {'search_options': search_options, 'display_options': display_options} if selected_object_type == x else {'search_options': {object_identifier_columns[object_type]: object_identifier}, 'display_options': default_display_options} for x in object_identifier_columns.keys()}

	# Get object data
	landing_data = {object_type: get_landing_data(object_identifier, object_type, Session(), tables, current_user.get_id())}

	# Get datasets
	if object_type != 'dataset':

		# Add data
		landing_data['datasets'] = search_database(associated_object_data['dataset']['search_options'], associated_object_data['dataset']['display_options'], 'dataset', Session(), tables)
 
	# Get tools
	if object_type != 'tool':

		# Add data
		landing_data['tools'] = search_database(associated_object_data['tool']['search_options'], associated_object_data['tool']['display_options'], 'tool', Session(), tables)

	# Get canned analyses
	if object_type != 'canned_analysis':

		# Add data
		landing_data['canned_analyses'] = search_database(associated_object_data['canned_analysis']['search_options'], associated_object_data['canned_analysis']['display_options'], 'canned_analysis', Session(), tables)

	return render_template('landing.html', landing_data=landing_data, object_type=object_type)

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

	# Check if user is authenticated
	if current_user.is_authenticated:

		# Get evaluation data
		evaluation_dict = request.form.to_dict()

		# Get object data
		object_info = {x: evaluation_dict.pop(x) for x in ['object_type', 'object_id']}

		# Get results dict
		melted_evaluation_dataframe = pd.Series(evaluation_dict).rename('score').to_frame()

		# Add columns
		melted_evaluation_dataframe['question_fk'] = [x.split('-')[2] for x in melted_evaluation_dataframe.index]

		# Add comment
		melted_evaluation_dataframe['column_type'] = ['comment' if 'comment' in x else 'score' for x in melted_evaluation_dataframe.index]

		# Cast
		evaluation_dataframe = pd.pivot_table(melted_evaluation_dataframe, index='question_fk', columns='column_type', values='score', aggfunc='first').reset_index()

		# Add user ID
		evaluation_dataframe['user_fk'] = current_user.get_id()
		
		# Add object FK
		evaluation_dataframe[object_info['object_type']+'_fk'] = object_info['object_id']

		print evaluation_dataframe

		# Create session
		# session = Session()

		# Try
		# try:

			# Upload evaluation
		engine.execute(tables['evaluation'].insert(), evaluation_dataframe.to_dict(orient='records'))


			# Commit
		# 	session.commit()

		# except:

		# 	# Rollback
		# 	session.rollback()

	# Get 
	return ''

#############################################
########## 2. Upload Analysis
#############################################

@app.route(entry_point+'/api/upload/analysis', methods=['POST'])
def upload_analysis_api():
	print 'uploading...'
	canned_analysis_dataframe = pd.read_table(StringIO(request.files['file'].read())).dropna()
	session = Session()
	upload_results = upload_analyses(canned_analysis_dataframe, engine, session)
	session.commit()
	return upload_results

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