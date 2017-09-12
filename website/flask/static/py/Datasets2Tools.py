#################################################################
#################################################################
############### Datasets2Tools API ##############################
#################################################################
#################################################################
##### Author: Denis Torre
##### Affiliation: Ma'ayan Laboratory,
##### Icahn School of Medicine at Mount Sinai

#################################################################
#################################################################
############### 1. Library Configuration ########################
#################################################################
#################################################################

#############################################
########## 1. Load libraries
#############################################
##### 1. Python modules #####
import json
import pandas as pd
import numpy as np

##### 2. Database modules #####
from sqlalchemy import or_, and_, func

#################################################################
#################################################################
############### 1. API Wrapper ##################################
#################################################################
#################################################################

#############################################
########## 1. Initialization
#############################################

class Datasets2Tools:

	def __init__(self, engine, sessionmaker, tables):
		
		# Save engine and tables
		self.engine = engine
		self.session = sessionmaker()
		self.tables = tables

#############################################
########## 2. Search
#############################################

	def search(self, search_filters, search_options, get_related_objects=False, get_fairness=False, user_id=None):

		# Try
		try:
			search_results = Search(self.engine, self.session, self.tables, search_filters, search_options, get_related_objects, get_fairness, user_id)
			self.session.commit()
		except:
			search_results = None
			self.session.rollback()
			raise

		# Return
		return search_results
			
#############################################
########## 3. Upload Analyses
#############################################

	def upload_analyses(self, uploaded_file, user_id):

		# Try
		try:
			upload_results = UploadAnalyses(self.engine, self.session, self.tables, uploaded_file, user_id)
			self.session.commit()
		except:
			upload_results = None
			self.session.rollback()
			raise

		# Return
		return upload_results
			
#############################################
########## 4. Upload Evaluation
#############################################

	def upload_evaluation(self, evaluation_scores):

		# Try
		try:
			UploadEvaluation(self.engine, self.tables, evaluation_scores)
			self.session.commit()
		except:
			self.session.rollback()
			raise

#################################################################
#################################################################
############### 2. Search API ###################################
#################################################################
#################################################################

#############################################
########## 1. Initialization
#############################################

class Search:

	def __init__(self, engine, session, tables, search_filters, search_options, get_related_objects, get_fairness, user_id):

		# Save query data
		self.engine, self.session, self.tables, self.object_type, sort_by, offset, page_size = engine, session, tables, search_options['object_type'], search_options['sort_by'], int(search_options['offset']), int(search_options['page_size'] )

		# Get IDs
		object_ids = self.get_ids(search_filters = search_filters.copy(), sort_by = sort_by)

		# Filter IDs
		filtered_ids = object_ids[(offset-1)*page_size:offset*page_size] if page_size and offset else object_ids

		# Get search results
		self.search_results = [self.get_object_data(object_id = object_id, get_related_objects = get_related_objects, get_fairness = get_fairness, user_id = user_id) for object_id in filtered_ids]
		self.search_filters = self.get_search_filters(object_ids = object_ids, used_filters = search_filters.keys())
		self.search_options = self.get_search_options(count = len(object_ids), sort_by = sort_by, offset = offset, page_size = page_size)

#############################################
########## 2. Get IDs
#############################################

	def get_ids(self, search_filters, sort_by):

		# Initialize query
		query = self.session.query(self.tables[self.object_type].columns['id']).distinct()

		# Expand query
		if self.object_type == 'dataset':
			query = query.join(self.tables['analysis_to_dataset']).join(self.tables['canned_analysis']).join(self.tables['analysis_to_tool']).join(self.tables['tool'])
		elif self.object_type == 'tool':
			query = query.join(self.tables['analysis_to_tool']).join(self.tables['canned_analysis']).join(self.tables['analysis_to_dataset']).join(self.tables['dataset'])
		elif self.object_type == 'canned_analysis':
			query = query.join(self.tables['analysis_to_dataset']).join(self.tables['dataset']).join(self.tables['analysis_to_tool']).join(self.tables['tool'])

		# Text search
		if 'q' in search_filters.keys():
			q = search_filters.pop('q')
			if self.object_type == 'dataset':
				query = query.filter(or_(self.tables['dataset'].columns['dataset_accession'].like(q), self.tables['dataset'].columns['dataset_title'].like(q), self.tables['dataset'].columns['dataset_description'].like(q)))
			elif self.object_type == 'tool':
				query = query.filter(or_(self.tables['tool'].columns['tool_name'].like(q), self.tables['tool'].columns['tool_description'].like(q)))
			elif self.object_type == 'canned_analysis':
				query = query.filter(or_(self.tables['canned_analysis'].columns['canned_analysis_accession'].like(q), self.tables['canned_analysis'].columns['canned_analysis_title'].like(q), self.tables['canned_analysis'].columns['canned_analysis_description'].like(q), self.tables['dataset'].columns['dataset_accession'].like(q), self.tables['tool'].columns['tool_name'].like(q)))

		# Keyword search
		if 'keyword' in search_filters.keys():
			keyword = search_filters.pop('keyword')
			query = query.filter(self.tables[self.object_type].columns['id'].in_(self.session.query(self.tables['keyword'].columns[self.object_type+'_fk']).distinct().filter(self.tables['keyword'].columns['keyword'] == keyword).subquery()))

		# Dataset search
		if 'dataset_accession' in search_filters.keys():
			dataset_accession = search_filters.pop('dataset_accession')
			query = query.filter(self.tables['dataset'].columns['dataset_accession'] == dataset_accession)

		# Tool search
		if 'tool_name' in search_filters.keys():
			tool_name = search_filters.pop('tool_name')
			query = query.filter(self.tables['tool'].columns['tool_name'] == tool_name)

		# Canned analysis search
		if 'canned_analysis_accession' in search_filters.keys():
			canned_analysis_accession = search_filters.pop('canned_analysis_accession')
			query = query.filter(self.tables['canned_analysis'].columns['canned_analysis_accession'] == canned_analysis_accession)

		# Metadata search
		if self.object_type == 'canned_analysis' and len(search_filters.keys()) > 0:
			for term_name, value in search_filters.iteritems():
				query = query.filter(self.tables['canned_analysis'].columns['id'].in_(self.session.query(self.tables['canned_analysis_metadata'].columns['canned_analysis_fk']).distinct() .join(self.tables['term']).filter(and_(self.tables['term'].columns['term_name'] == term_name, self.tables['canned_analysis_metadata'].columns['value'] == value)).subquery()))
			
		# Sort by relevance
		if sort_by == 'relevance':
			if self.object_type == 'dataset':
				pass
			elif self.object_type == 'tool':
				pass
			elif self.object_type == 'canned_analysis':
				pass
			
		# Sort by date
		if sort_by == 'date':
			pass
			# query = query.order_by(self.tables['object_type'].columns['date'].desc())
							
		# Sort by FAIRness
		if sort_by == 'fairness':
			if self.object_type == 'dataset':
				pass
			elif self.object_type == 'tool':
				pass
			elif self.object_type == 'canned_analysis':
				pass

		# Get IDs
		ids = [x[0] for x in query.all()]

		# Get query
		return ids

#############################################
########## 3. Get Object Data
#############################################

	def get_object_data(self, object_id, get_related_objects, get_fairness, user_id):

		# Dataset
		if self.object_type == 'dataset':

			# Get dataset data
			dataset_query = self.session.query(self.tables['dataset'], self.tables['repository']).join(self.tables['repository']).filter(self.tables['dataset'].columns['id'] == object_id).all()
			object_data = [x._asdict() for x in dataset_query][0]

		# Tool
		elif self.object_type == 'tool':
			
			# Get tool data
			tool_query = self.session.query(self.tables['tool']).filter(self.tables['tool'].columns['id'] == object_id)
			object_data = {key: value for key, value in zip(self.tables[self.object_type].columns.keys(), tool_query.all()[0])}

			# Get article data
			article_query = self.session.query(self.tables['article'], self.tables['journal']).join(self.tables['journal']).filter(self.tables['article'].columns['tool_fk'] == object_id).all()
			object_data['articles'] = [x._asdict() for x in article_query]

			# Convert article abstracts
			for i in range(len(object_data['articles'])):
				object_data['articles'][i]['abstract'] = json.loads(object_data['articles'][i]['abstract'])

		# Canned Analysis
		elif self.object_type == 'canned_analysis':
					
			# Perform analysis query
			canned_analysis_query = self.session.query(self.tables['canned_analysis'], self.tables['tool'], self.tables['dataset'], self.tables['repository']).join(self.tables['analysis_to_tool']).join(self.tables['tool']).join(self.tables['analysis_to_dataset']).join(self.tables['dataset']).join(self.tables['repository']).filter(self.tables['canned_analysis'].columns['id'] == object_id).all()
			object_data = [x._asdict() for x in canned_analysis_query][0]

			# Perform metadata query
			canned_analysis_metadata_query = self.session.query(self.tables['canned_analysis_metadata'].columns['value'], self.tables['term'].columns['term_name']).join(self.tables['term']).filter(self.tables['canned_analysis_metadata'].columns['canned_analysis_fk'] == object_id).all()
			object_data['metadata'] = pd.DataFrame([metadata_query_result._asdict() for metadata_query_result in canned_analysis_metadata_query]).set_index('term_name').to_dict()['value']

		# Keywords
		keyword_query = self.session.query(self.tables['keyword'].columns['keyword']).filter(self.tables['keyword'].columns[self.object_type+'_fk'] == object_id).all()
		object_data['keywords'] = [x[0] for x in keyword_query]

		# Get related objects
		if get_related_objects:

			# Perform related object query
			related_object_query = self.session.query(self.tables['related_'+self.object_type].columns['_'.join(['target', self.object_type,'fk'])]).filter(self.tables['related_'+self.object_type].columns['_'.join(['source', self.object_type,'fk'])] == object_id)
			object_data['related_objects'] = [self.get_object_data(x[0], get_related_objects=False, get_fairness=False, user_id=None) for x in related_object_query.all()]

		# Get FAIRness
		if get_fairness:

			# Add dict
			object_data['fairness'] = {}

			# Get questions
			questions_query = self.session.query(self.tables['question']).filter(self.tables['question'].columns['object_type'] == self.object_type).all()
			object_data['fairness']['questions'] = [x._asdict() for x in questions_query]
			question_ids = [x.get('id') for x in object_data['fairness']['questions']]

			# Evaluation queries (data not extracted)
			all_evaluations_query = self.session.query(self.tables[self.object_type+'_evaluation']).filter(self.tables[self.object_type+'_evaluation'].columns[self.object_type+'_fk'] == object_id)
			user_evaluations_query = all_evaluations_query.filter(self.tables[self.object_type+'_evaluation'].columns['user_fk'] == user_id)

			# Add user evaluation
			object_data['fairness']['user_evaluation'] = pd.DataFrame(user_evaluations_query.all()).set_index('question_fk')[['score', 'comment']].to_dict(orient='index') if len(user_evaluations_query.all()) > 0 else {x:{} for x in question_ids}

			# Add all evaluations
			if len(all_evaluations_query.all()) > 0:
				all_evaluations_dict = pd.DataFrame(all_evaluations_query.all()).groupby('question_fk').aggregate(lambda x: list(x)).to_dict(orient='index')
				all_evaluations = {question_id: {'average_score': np.mean(all_evaluations_dict[question_id]['score']), 'comments': all_evaluations_dict[question_id]['comment']} for question_id in question_ids}
				nr_evaluations = max([len(x['user_fk']) for x in all_evaluations_dict.values()])
			else:
				all_evaluations = {x: {} for x in question_ids}
				nr_evaluations = 0
			object_data['fairness']['all_evaluations'] = all_evaluations
			object_data['fairness']['evaluations'] = nr_evaluations

		# Return
		return object_data

#############################################
########## 4. Get Search Filters
#############################################

	def get_search_filters(self, object_ids, used_filters):

		# Define object identifiers
		object_identifiers = {'dataset': 'dataset_accession', 'tool': 'tool_name'}

		# Define search filters
		search_filters = []

		# Add keywords
		search_filters.append({
			'label': 'keyword',
			'values': self.session.query(self.tables['keyword'].columns['keyword']).filter(self.tables['keyword'].columns[self.object_type+'_fk'].in_(object_ids)).distinct().all()
		})

		# Get datasets and tools other object type
		if self.object_type == 'dataset' or self.object_type == 'tool':
			other_object_type = 'dataset' if self.object_type == 'tool' else 'tool'
			search_filters.append({
				'label': object_identifiers[other_object_type],
				'values': [x[0] for x in self.session.query(self.tables[other_object_type].columns[object_identifiers[other_object_type]]).join(self.tables['analysis_to_'+other_object_type]).join(self.tables['canned_analysis']).join(self.tables['analysis_to_'+self.object_type]).join(self.tables[self.object_type]).filter(self.tables[self.object_type].columns['id'].in_(object_ids)).distinct().all()]
			})

		# Get canned analysis data
		elif self.object_type == 'canned_analysis':

			# Get datasets and tools
			for associated_object_type in ['dataset', 'tool']:
				search_filters.append({
					'label': object_identifiers[associated_object_type],
					'values': [x[0] for x in self.session.query(self.tables[associated_object_type].columns[object_identifiers[associated_object_type]]).join(self.tables['analysis_to_'+associated_object_type]).join(self.tables['canned_analysis']).distinct().all()]
				})

			# Perform metadata query
			metadata_query = self.session.query(self.tables['term'].columns['term_name'], self.tables['canned_analysis_metadata'].columns['value']).join(self.tables['canned_analysis_metadata']).filter(self.tables['canned_analysis_metadata'].columns['canned_analysis_fk'].in_(object_ids)).distinct().all()
			

			# Add metadata
			if len(metadata_query) > 0:
				metadata_dataframe = pd.DataFrame(metadata_query).set_index('term_name')
				for term_name in metadata_dataframe.index.unique():
					search_filters.append({
						'label': term_name,
						'values': metadata_dataframe.loc[term_name, 'value'].tolist() if isinstance(metadata_dataframe.loc[term_name, 'value'], pd.Series) else [metadata_dataframe.loc[term_name, 'value']]
					})

		# Filter filters (so meta)
		search_filters = [x for x in search_filters if len(x['values']) > 1 or x['label'] in used_filters]

		# Return
		return search_filters

#############################################
########## 5. Get Search Options
#############################################

	def get_search_options(self, count, sort_by, offset, page_size):

		# Define search options
		search_options = {'count': count}

		# Get max pages
		max_pages = -(-count//page_size)

		# Get offset options
		offset_options = [offset-1, offset, offset+1, max_pages]

		# Get offsets
		search_options['offset'] = {'values': [x for x in set(offset_options) if x > 0 and x <= max_pages], 'selected': offset}

		# Default options
		search_options['sort_by'] = {'values': [{'label': 'Relevance', 'value': 'relevance'}, {'label': 'Date (newest)', 'value': 'newest'}], 'selected': sort_by}

		# Get sort by
		if self.object_type == 'dataset':
			search_options['sort_by']['values'].append([])
		elif self.object_type == 'tool':
			search_options['sort_by']['values'].append([])
		elif self.object_type == 'canned_analysis':
			search_options['sort_by']['values'].append([])

		# Get page sizes
		page_sizes = [(x+1)*10 for x in range(min(count/10, 3)+1)] if count > 10 else []
		search_options['page_size'] = {'values': page_sizes, 'selected': page_size}
		
		# Return
		return search_options

#################################################################
#################################################################
############### 3. Upload Analysis API ##########################
#################################################################
#################################################################

#############################################
########## 1. Initialization
#############################################

class UploadAnalyses:

	def __init__(self, engine, session, tables, uploaded_file, user_id):

		# Save query data and identifiers
		self.engine, self.session, self.tables, self.table_conversion = engine, session, tables, {'datasets': {'table': 'dataset', 'unique_column': 'dataset_accession'}, 'tools': {'table': 'tool', 'unique_column': 'tool_name'}, 'canned_analysis_url': {'table': 'canned_analysis', 'unique_column': 'canned_analysis_url'}}

		# Read file
		canned_analysis_dataframe = self.read_uploaded_file(uploaded_file).drop_duplicates()

		# Get object IDs
		for column in ['datasets', 'tools', 'canned_analysis_url']:
			canned_analysis_dataframe = self.get_object_ids(canned_analysis_dataframe = canned_analysis_dataframe, column = column)

		# Upload object relationships
		self.upload_object_relationships(canned_analysis_ids = canned_analysis_dataframe['canned_analysis_fk'], dataset_ids = canned_analysis_dataframe['dataset_fk'], tool_ids = canned_analysis_dataframe['tool_fk'], )

		# Upload metadata
		self.upload_metadata(canned_analysis_ids = canned_analysis_dataframe['canned_analysis_fk'], canned_analysis_metadata = canned_analysis_dataframe['metadata'])

		# Get canned analysis IDs
		upload_results = str(canned_analysis_dataframe['canned_analysis_fk'])

		# Return IDs
		return upload_results

#############################################
########## 2. Read Uploaded File
#############################################

	def read_uploaded_file(self, uploaded_file):

		pass

#############################################
########## 3. Get Object Ids
#############################################

	def get_object_ids(self, canned_analysis_dataframe, column):

		pass

#############################################
########## 4. Upload Object Relationships
#############################################

	def upload_object_relationships(self, canned_analysis_ids, dataset_ids, tool_ids):

		pass

#############################################
########## 5. Upload Analysis Metadata
#############################################

	def upload_metadata(self, canned_analysis_ids, canned_analysis_metadata):

		pass

#################################################################
#################################################################
############### 4. Upload Evaluation API ########################
#################################################################
#################################################################

#############################################
########## 1. Initialization
#############################################

class UploadEvaluation:

	def __init__(self, engine, tables, evaluation_scores):

		# Get evaluation info
		evaluation_info = {x: evaluation_scores.pop(x) for x in ['user_id', 'object_type', 'object_id']}

		# Prepare dataframe
		score_dataframe = self.prepare_score_dataframe(evaluation_scores = evaluation_scores, evaluation_info = evaluation_info)
		# print score_dataframe

		# Upload
		engine.execute(tables[evaluation_info['object_type']+'_evaluation'].insert().prefix_with('IGNORE'), score_dataframe.to_dict(orient='records'))

#############################################
########## 2. Prepare Score Dataframe
#############################################

	def prepare_score_dataframe(self, evaluation_scores, evaluation_info):

		# Convert to dataframe
		melted_score_dataframe = pd.Series(evaluation_scores).rename('score').to_frame()

		# Add columns
		melted_score_dataframe['question_fk'] = [x.split('-')[2] for x in melted_score_dataframe.index]
		melted_score_dataframe['column_type'] = ['comment' if 'comment' in x else 'score' for x in melted_score_dataframe.index]

		# Cast
		score_dataframe = pd.pivot_table(melted_score_dataframe, index='question_fk', columns='column_type', values='score', aggfunc='first').reset_index().fillna('')

		# Add data
		score_dataframe['user_fk'] = evaluation_info['user_id']
		score_dataframe[evaluation_info['object_type']+'_fk'] = evaluation_info['object_id']

		# Return
		return score_dataframe

#################################################################
#################################################################
############### 5. API ##########################################
#################################################################
#################################################################

#############################################
########## 1. Initialization
#############################################