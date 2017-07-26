############################################################
############################################################
############### Datasets2Tools Web Interface ###############
############################################################
############################################################

#######################################################
########## 1. Setup Python ############################
#######################################################

##############################
##### 1.1 Python Libraries
##############################
import sys, json, os, urllib2
import pandas as pd
from flask import Flask, render_template, render_template_string, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy

##############################
##### 1.2 Custom Libraries
##############################
scripts_path = '/datasets2tools/flask/scripts'
if os.path.exists(scripts_path):
	sys.path.append(scripts_path)
else:
	sys.path.append(os.path.basename(scripts_path))

##############################
##### 1.3 Setup App
##############################
# Set route
entry_point = '/datasets2tools-dev'

# Initialize Flask App
static_path = '/datasets2tools/flask/static'
if os.path.exists(static_path):
	app = Flask(__name__, static_url_path=static_path)
else:
	app = Flask(__name__)


# Read data
connection_file = '../../../datasets2tools-database/f1-mysql.dir/conn.json'
if os.path.exists(connection_file):
	with open(connection_file) as openfile:
		connectionDict = json.loads(openfile.read())['phpmyadmin']
	os.environ['DB_USER'] = connectionDict['username']
	os.environ['DB_PASS'] = connectionDict['password']
	os.environ['DB_HOST'] = connectionDict['host']
	os.environ['DB_NAME'] = 'datasets2tools_dev'

# Initialize database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + os.environ['DB_USER'] + ':' + os.environ['DB_PASS'] + '@' + os.environ['DB_HOST'] + '/' + os.environ['DB_NAME']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 290
engine = SQLAlchemy(app).engine

#######################################################
########## 2. Platform ################################
#######################################################

##############################
##### 1. Templates
##############################

#########################
### 1. Homepage
#########################

@app.route(entry_point+'/')
@app.route(entry_point+'')

def index():

	# Render template
	return render_template('index.html')


#######################################################
########## 3. Run Flask App ###########################
#######################################################
# Run App
if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')