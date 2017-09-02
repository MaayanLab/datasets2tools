# Modules
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import os, json, random, sys
from sqlalchemy.exc import IntegrityError
from flask_dropzone import Dropzone
from StringIO import StringIO
from flask_sqlalchemy import SQLAlchemy
sys.path.append('static/py')
from upload_API import *
from search_API import *
from sqlalchemy.orm import sessionmaker

# Configure
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:MyNewPass@localhost/datasets2tools?charset=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['DROPZONE_MAX_FILE_SIZE'] = 10
db = SQLAlchemy(app)
engine = db.engine
entry_point = '/datasets2tools'
dropzone = Dropzone(app)
metadata = MetaData()
metadata.reflect(bind=engine)
Session = sessionmaker(bind=engine)

# Lists
fairness = [{"fairness_question": "The tool is hosted in one or more well-used repositories, if relevant repositories exist.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Source code is shared on a public repository.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Code is written in an open-source, free programming language.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "The tool inputs standard data format(s) consistent with community practice.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "All previous versions of the tool are made available.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Web-based version is available (in addition to desktop version).", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Source code is documented.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Pipelines that use the tool have been standardized and provide detailed usage guidelines.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "A tutorial page is provided for the tool.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Example datasets are provided.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Licensing information is provided on the tool's landing page.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Information is provided describing how to cite the tool.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Version information is provided for the tool.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "A paper about the tool has been published.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Video tutorials for the tool are available.", "fairness_score": random.uniform(-1, 1)}, {"fairness_question": "Contact information is provided for the originator(s) of the tool.", "fairness_score": random.uniform(-1, 1)}]
search_filters = {'tools': ['Enrichr', 'L1000CDS2', 'GeneMANIA'], 'datasets': ['GSE68203', 'GSE68207', 'GSE30017'], 'keywords': ['enrichment', 'genome', 'cancer'], 'canned_analysis_metadata': {'geneset': ['upregulated', 'downregulated'], 'genes': ['100', '200', '500'], 'cell_line': ['HEK293', 'MCF10A', 'MCF7']}}
tools = {'search_filters':{x:search_filters[x] for x in ['datasets', 'keywords']}, 'count': 5, 'search_results':[{'tool_name': 'Enrichr','fairness':fairness,'publications':[{'journal': 'BMC Bioinformatics', 'keywords': ['enrichment', 'analysis', 'interactive'],'year': 2017, 'month':'April', 'doi': '10.1186/1471-2105-14-128', 'publication_title': 'Enrichr: interactive and collaborative HTML5 gene list enrichment analysis tool.', 'authors': 'Chen EY, Tan CM, Kou Y, Duan Q, Wang Z, Meirelles GV, Clark NR, Ma\'ayan A', 'abstract': 'System-wide profiling of genes and proteins in mammalian cells produce lists of differentially expressed genes/proteins that need to be further analyzed for their collective functions in order to extract new knowledge. Once unbiased lists of genes or proteins are generated from such experiments, these lists are used as input for computing enrichment with existing lists created from prior knowledge organized into gene-set libraries. While many enrichment analysis tools and gene-set libraries databases have been developed, there is still room for improvement.'}, {'journal': 'Bioinformatics', 'year': 2014}],'keywords':['enrichment', 'visualization'], 'date':'May 27th, 2017','tool_icon_url': 'http://amp.pharm.mssm.edu/Enrichr/images/enrichr-icon.png','tool_description': 'An enrichment analysis tool with over 90 libraries.','has_scripts': True, 'tool_homepage_url': 'http://amp.pharm.mssm.edu/Enrichr/', 'related_objects': [{'tool_name': 'Enrichr','publications':[{'journal': 'BMC Bioinformatics', 'keywords': ['enrichment', 'analysis', 'interactive'],'year': 2017, 'month':'April', 'doi': '10.1186/1471-2105-14-128', 'publication_title': 'Enrichr: interactive and collaborative HTML5 gene list enrichment analysis tool.', 'authors': 'Chen EY, Tan CM, Kou Y, Duan Q, Wang Z, Meirelles GV, Clark NR, Ma\'ayan A', 'abstract': 'System-wide profiling of genes and proteins in mammalian cells produce lists of differentially expressed genes/proteins that need to be further analyzed for their collective functions in order to extract new knowledge. Once unbiased lists of genes or proteins are generated from such experiments, these lists are used as input for computing enrichment with existing lists created from prior knowledge organized into gene-set libraries. While many enrichment analysis tools and gene-set libraries databases have been developed, there is still room for improvement.'}, {'journal': 'Bioinformatics', 'year': 2014}],'keywords':['enrichment', 'visualization'], 'date':'May 27th, 2017','tool_icon_url': 'http://amp.pharm.mssm.edu/Enrichr/images/enrichr-icon.png','tool_description': 'An enrichment analysis tool with over 90 libraries.','has_scripts': True, 'tool_homepage_url': 'http://amp.pharm.mssm.edu/Enrichr/'}]},{'tool_name': 'L1000CDS2','date':'May 27th, 2017','tool_icon_url': 'http://amp.pharm.mssm.edu/Enrichr/images/enrichr-icon.png','tool_description': 'An enrichment analysis tool with over 90 libraries.','has_scripts': True},{'tool_name': 'GeneMANIA','date':'May 27th, 2017','tool_icon_url': 'http://amp.pharm.mssm.edu/Enrichr/images/enrichr-icon.png','tool_description': 'An enrichment analysis tool with over 90 libraries.','has_scripts': True}]}
canned_analyses = {'search_filters': search_filters, 'count': 7, 'search_results': [{'fairness':fairness,'canned_analysis_description':'The analysis explores the gene interaction network and pathway enrichment of the top 50 most upregulated genes identified by applying the Characteristic Direction method comparing gene expression between cells affected by nasopharynx carcinoma and healthy control cells in the  Nasopharyngeal biopsies (with Epstein-Barr virus (EBV)-positive undifferentiated NPC)  cell type.','date':'May 27th, 2017','canned_analysis_accession':'DCA0000178','canned_analysis_url':'https://github.com/denis-torre/images/blob/master/genemania/1.png?raw=true','canned_analysis_preview_url': 'https://github.com/denis-torre/images/blob/master/genemania/1.png?raw=true','canned_analysis_title': 'Enrichment analysis of genes upregulated in cancer','tools': [{'tool_name': 'GeneMANIA','tool_icon_url': 'https://pbs.twimg.com/profile_images/720745173970460672/psYcEwIT_400x400.jpg'},{'tool_name': 'Enrichr','tool_icon_url': 'http://amp.pharm.mssm.edu/Enrichr/images/enrichr-icon.png'},{'tool_name': 'L1000CDS2','tool_icon_url': 'http://amp.pharm.mssm.edu/L1000CDS2/CSS/images/sigine.png'}],'datasets': [{'dataset_accession': 'GSE68203','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'},{'dataset_accession': 'GSE68205','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'},{'dataset_accession': 'GSE68209','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'}],'metadata': {'alpha': 'beta','gamma': 'delta','epsilon': 'zeta'}, 'keywords': ['cancer', 'enrichment', 'upregulated'], 'related_objects': [{'canned_analysis_description':'The analysis explores the gene interaction network and pathway enrichment of the top 50 most upregulated genes identified by applying the Characteristic Direction method comparing gene expression between cells affected by nasopharynx carcinoma and healthy control cells in the  Nasopharyngeal biopsies (with Epstein-Barr virus (EBV)-positive undifferentiated NPC)  cell type.','date':'May 27th, 2017','canned_analysis_accession':'DCA0000178','canned_analysis_url':'https://github.com/denis-torre/images/blob/master/genemania/1.png?raw=true','canned_analysis_preview_url': 'https://github.com/denis-torre/images/blob/master/genemania/1.png?raw=true','canned_analysis_title': 'Enrichment analysis of genes upregulated in cancer','tools': [{'tool_name': 'GeneMANIA','tool_icon_url': 'https://pbs.twimg.com/profile_images/720745173970460672/psYcEwIT_400x400.jpg'},{'tool_name': 'Enrichr','tool_icon_url': 'http://amp.pharm.mssm.edu/Enrichr/images/enrichr-icon.png'},{'tool_name': 'L1000CDS2','tool_icon_url': 'http://amp.pharm.mssm.edu/L1000CDS2/CSS/images/sigine.png'}],'datasets': [{'dataset_accession': 'GSE68203','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'},{'dataset_accession': 'GSE68205','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'},{'dataset_accession': 'GSE68209','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'}],'metadata': {'alpha': 'beta','gamma': 'delta','epsilon': 'zeta'}, 'keywords': ['cancer', 'enrichment', 'upregulated']}]}, {'canned_analysis_description':'The analysis explores the gene interaction network and pathway enrichment of the top 50 most upregulated genes identified by applying the Characteristic Direction method comparing gene expression between cells affected by nasopharynx carcinoma and healthy control cells in the  Nasopharyngeal biopsies (with Epstein-Barr virus (EBV)-positive undifferentiated NPC)  cell type.','date':'May 27th, 2017','canned_analysis_accession':'DCA0000178','canned_analysis_url':'https://github.com/denis-torre/images/blob/master/genemania/1.png?raw=true','canned_analysis_preview_url': 'https://github.com/denis-torre/images/blob/master/genemania/1.png?raw=true','canned_analysis_title': 'Enrichment analysis of genes downregulated','tools': [{'tool_name': 'GeneMANIA','tool_icon_url': 'https://pbs.twimg.com/profile_images/720745173970460672/psYcEwIT_400x400.jpg'},{'tool_name': 'Enrichr','tool_icon_url': 'http://amp.pharm.mssm.edu/Enrichr/images/enrichr-icon.png'},{'tool_name': 'L1000CDS2','tool_icon_url': 'http://amp.pharm.mssm.edu/L1000CDS2/CSS/images/sigine.png'}],'datasets': [{'dataset_accession': 'GSE68203','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'},{'dataset_accession': 'GSE68205','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'},{'dataset_accession': 'GSE68209','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'}],'metadata': {'geneset': 'upregulated','gamma': 'delta','epsilon': 'zeta'}, 'keywords': ['cancer', 'enrichment', 'upregulated'], 'related_objects': [{'canned_analysis_description':'The analysis explores the gene interaction network and pathway enrichment of the top 50 most upregulated genes identified by applying the Characteristic Direction method comparing gene expression between cells affected by nasopharynx carcinoma and healthy control cells in the  Nasopharyngeal biopsies (with Epstein-Barr virus (EBV)-positive undifferentiated NPC)  cell type.','date':'May 27th, 2017','canned_analysis_accession':'DCA0000178','canned_analysis_url':'https://github.com/denis-torre/images/blob/master/genemania/1.png?raw=true','canned_analysis_preview_url': 'https://github.com/denis-torre/images/blob/master/genemania/1.png?raw=true','canned_analysis_title': 'Enrichment analysis of genes downregulated in cancer','tools': [{'tool_name': 'GeneMANIA','tool_icon_url': 'https://pbs.twimg.com/profile_images/720745173970460672/psYcEwIT_400x400.jpg'},{'tool_name': 'Enrichr','tool_icon_url': 'http://amp.pharm.mssm.edu/Enrichr/images/enrichr-icon.png'},{'tool_name': 'L1000CDS2','tool_icon_url': 'http://amp.pharm.mssm.edu/L1000CDS2/CSS/images/sigine.png'}],'datasets': [{'dataset_accession': 'GSE68203','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'},{'dataset_accession': 'GSE68205','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'},{'dataset_accession': 'GSE68209','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif'}],'metadata': {'geneset': 'downregulated','gamma': 'asdsdf','epsilon': 'zedsfgsfdgdsta'}, 'keywords': ['cancer', 'enrichment', 'downregulated']}]}]}
datasets = {'search_filters':{x:search_filters[x] for x in ['tools', 'keywords']}, 'count': 3, 'search_results':[{'dataset_accession': 'GSE68203','fairness':fairness,'keywords': ['genome', 'Pol II', 'worms'],'dataset_type': 'RNA-Seq','dataset_title': 'Genome-wide RNA Pol II-CTD occupancy in wild type and mutant worms','dataset_description': 'We used RNA Pol II-CTD occupancy assay to identify mRNA isoform switch in mutant animals compared to wild type animals.','repository_name': 'Gene Expression Omnibus','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif','repository_homepage_url': 'https://www.ncbi.nlm.nih.gov/geo/','date': 'May 27th, 2017', 'dataset_landing_url': 'https://www.ncbi.nlm.nih.gov/geo/', 'related_objects': [{'dataset_accession': 'GSE68203','keywords': ['genome', 'Pol II', 'worms'],'dataset_type': 'RNA-Seq','dataset_title': 'Genome-wide RNA Pol II-CTD occupancy in wild type and mutant worms','dataset_description': 'We used RNA Pol II-CTD occupancy assay to identify mRNA isoform switch in mutant animals compared to wild type animals.','repository_name': 'Gene Expression Omnibus','repository_icon_url': 'https://www.ncbi.nlm.nih.gov/geo/img/geo_main.gif','repository_homepage_url': 'https://www.ncbi.nlm.nih.gov/geo/','date': 'May 27th, 2017', 'dataset_landing_url': 'https://www.ncbi.nlm.nih.gov/geo/'}]}]}

# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(15), unique=True)
	email = db.Column(db.String(50), unique=True)
	password = db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

@app.route(entry_point+'/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

# Routes
@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.route(entry_point)
def index():
	return render_template('index.html')

@app.route(entry_point+'/landing/<object_type>/<object_identifier>')
def landing(object_type, object_identifier):
	session = Session()
	if object_type == 'dataset':
		landing_data = {
			'dataset': search_database({'dataset_accession': object_identifier}, object_type, session, metadata, get_related=True)[0],
			'canned_analyses': {'search_filters': canned_analyses['search_filters'], 'count': 1, 'search_results': search_database({'dataset_accession': object_identifier}, 'canned_analysis', session, metadata)},
			'tools': {'search_filters': tools['search_filters'], 'count': 1, 'search_results': search_database({'dataset_accession': object_identifier}, 'tool', session, metadata)}
		}
	elif object_type == 'tool':
		landing_data = {
			'datasets': {'search_filters': tools['search_filters'], 'count': 1, 'search_results': search_database({'tool_name': object_identifier}, 'dataset', session, metadata)},
			'canned_analyses': {'search_filters': canned_analyses['search_filters'], 'count': 1, 'search_results': search_database({'tool_name': object_identifier}, 'canned_analysis', session, metadata)},
			'tool': search_database({'tool_name': object_identifier}, object_type, session, metadata, get_related=True)[0]
		}
	elif object_type == 'canned_analysis':
		landing_data = {
			'datasets': {'search_filters': datasets['search_filters'], 'count': 1, 'search_results': search_database({'canned_analysis_fk': 1}, 'dataset', session, metadata)},
			'canned_analysis': search_database({'id': 1}, object_type, session, metadata, get_related=True)[0],
			'tools': {'search_filters': tools['search_filters'], 'count': 1, 'search_results': search_database({'canned_analysis_fk': 1}, 'tool', session, metadata)}
		}
	else:
		abort(404)
	offset = request.args.get('offset', default=1, type=int)
	page_size = request.args.get('page_size', default=10, type=int)
	sort_by = request.args.get('sort_by', default='relevance', type=str)
	q = request.args.get('q', default='', type=str)
	session.close()
	return render_template('landing.html', landing_data=landing_data, object_type=object_type, offset=offset, page_size=page_size, sort_by=sort_by, q=q)

@app.route(entry_point+'/search')
def search():
	session=Session()
	search_options_dict = {
		'offset': request.args.get('offset', default=1, type=int),
		'page_size': request.args.get('page_size', default=10, type=int),
		'sort_by': request.args.get('sort_by', default='relevance', type=str),
		'object_type': request.args.get('object_type', default='canned_analysis', type=str)
	}
	query_dict = {key:value for key, value in request.args.to_dict().iteritems() if key not in search_options_dict.keys()}
	if search_options_dict['object_type']=='canned_analysis':
		search_data=canned_analyses
	elif search_options_dict['object_type']=='dataset':
		search_data=datasets
	elif search_options_dict['object_type']=='tool':
		search_data=tools
	search_data['search_results'] = search_database(query_dict, search_options_dict, session, metadata, get_related=False)
	session.close()
	return render_template('search.html', search_data=search_data, object_type=search_options_dict['object_type'], search_options_dict=search_options_dict, offset=1, page_size=10, sort_by='relevance')

@app.route(entry_point+'/contribute')
def contribute():
	return render_template('contribute.html')

@app.route(entry_point+'/testsearch')
def testsearch():
	session = Session()
	query_dict = request.args.to_dict()
	object_type = query_dict.pop('object_type')
	results = json.dumps(search_database(query_dict, object_type, session, metadata))
	session.close()
	return results

@app.route(entry_point+'/api/upload/analysis', methods=['POST'])
def upload_analysis_api():
	print 'uploading...'
	canned_analysis_dataframe = pd.read_table(StringIO(request.files['file'].read())).dropna()
	session = Session()
	upload_results = upload_analyses(canned_analysis_dataframe, engine, session)
	session.commit()
	return upload_results

@app.route(entry_point+'/static/<path:path>')
def static_files(path):
	return send_from_directory('static', path)


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')