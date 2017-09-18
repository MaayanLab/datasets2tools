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
import json, os
import pandas as pd
import numpy as np
from datetime import datetime

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

	def upload_analyses(self, analysis_file, user_id):

		# Try
		try:
			upload_results = UploadAnalyses(self.engine, self.session, self.tables, analysis_file, user_id)
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
			
#############################################
########## 5. Update Database
#############################################

	def update_database(self, file_directory):

		# Try
		try:
			UpdateDatabase(self.engine, self.session, self.tables, file_directory)
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
			query = query.outerjoin(self.tables['analysis_to_dataset']).outerjoin(self.tables['canned_analysis']).outerjoin(self.tables['analysis_to_tool']).outerjoin(self.tables['tool'])
		elif self.object_type == 'tool':
			query = query.outerjoin(self.tables['analysis_to_tool']).outerjoin(self.tables['canned_analysis']).outerjoin(self.tables['analysis_to_dataset']).outerjoin(self.tables['dataset']).outerjoin(self.tables['article']).filter(self.tables['tool'].columns['display'] == True)
		elif self.object_type == 'canned_analysis':
			query = query.join(self.tables['analysis_to_dataset']).join(self.tables['dataset']).join(self.tables['analysis_to_tool']).join(self.tables['tool'])

		# Text search
		if 'q' in search_filters.keys():
			q = '%'+search_filters.pop('q')+'%'
			if self.object_type == 'dataset':
				query = query.filter(or_(self.tables['dataset'].columns['dataset_accession'].like(q), self.tables['dataset'].columns['dataset_title'].like(q), self.tables['dataset'].columns['dataset_description'].like(q)))
			elif self.object_type == 'tool':
				query = query.filter(or_(self.tables['tool'].columns['tool_name'].like(q), self.tables['tool'].columns['tool_description'].like(q), self.tables['article'].columns['article_title'].like(q), self.tables['article'].columns['authors'].like(q), self.tables['article'].columns['abstract'].like(q)))
			elif self.object_type == 'canned_analysis':
				query = query.filter(or_(self.tables['canned_analysis'].columns['canned_analysis_accession'].like(q), self.tables['canned_analysis'].columns['canned_analysis_title'].like(q), self.tables['canned_analysis'].columns['canned_analysis_description'].like(q), self.tables['dataset'].columns['dataset_accession'].like(q), self.tables['tool'].columns['tool_name'].like(q), self.tables['dataset'].columns['dataset_title'].like(q),  self.tables['dataset'].columns['dataset_description'].like(q), ))

		# Keyword search
		if 'keyword' in search_filters.keys():
			keyword = search_filters.pop('keyword')
			query = query.filter(self.tables[self.object_type].columns['id'].in_(self.session.query(self.tables[self.object_type+'_keyword'].columns[self.object_type+'_fk']).distinct().filter(self.tables[self.object_type+'_keyword'].columns['keyword'] == keyword).subquery()))

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
				query = query.outerjoin(self.tables['article_metrics']).group_by(self.tables['tool'].columns['tool_name']).order_by(func.count(self.tables['analysis_to_tool'].columns['tool_fk']).desc(), self.tables['article_metrics'].columns['attention_score'].desc())
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

			# Add analyses
			object_data['analyses'] = self.session.query(func.count(self.tables['analysis_to_dataset'].columns['dataset_fk'])).filter(self.tables['analysis_to_dataset'].columns['dataset_fk'] == object_id).all()[0][0]

		# Tool
		elif self.object_type == 'tool':
			
			# Get tool data
			tool_query = self.session.query(self.tables['tool']).filter(self.tables['tool'].columns['id'] == object_id)
			object_data = {key: value for key, value in zip(self.tables[self.object_type].columns.keys(), tool_query.all()[0])}

			# Get metrics
			tool_metrics_query = self.session.query(self.tables['article_metrics'].columns['citations'], self.tables['article_metrics'].columns['altmetric_badge_url'], self.tables['article_metrics'].columns['attention_score']).join(self.tables['article']).join(self.tables['tool']).filter(self.tables['tool'].columns['id'] == object_id).all()
			try:
				object_data.update(pd.DataFrame(tool_metrics_query).T.to_dict()[0])
			except:
				pass

			# Get article data
			article_query = self.session.query(self.tables['article'], self.tables['journal']).join(self.tables['journal']).filter(self.tables['article'].columns['tool_fk'] == object_id).all()
			object_data['articles'] = [x._asdict() for x in article_query]

			# Convert article abstracts
			for i in range(len(object_data['articles'])):
				object_data['articles'][i]['abstract'] = json.loads(object_data['articles'][i]['abstract'])

			# Add analyses
			object_data['analyses'] = self.session.query(func.count(self.tables['analysis_to_tool'].columns['tool_fk'])).filter(self.tables['analysis_to_tool'].columns['tool_fk'] == object_id).all()[0][0]

		# Canned Analysis
		elif self.object_type == 'canned_analysis':
					
			# Perform analysis query
			canned_analysis_query = self.session.query(self.tables['canned_analysis'], self.tables['tool'], self.tables['dataset'], self.tables['repository'], self.tables['user'].columns['username']).join(self.tables['analysis_to_tool']).join(self.tables['tool']).join(self.tables['analysis_to_dataset']).join(self.tables['dataset']).join(self.tables['repository']).join(self.tables['contribution']).join(self.tables['user']).filter(self.tables['canned_analysis'].columns['id'] == object_id).all()
			object_data = [x._asdict() for x in canned_analysis_query][0]

			# Perform metadata query
			canned_analysis_metadata_query = self.session.query(self.tables['canned_analysis_metadata'].columns['value'], self.tables['term'].columns['term_name']).join(self.tables['term']).filter(self.tables['canned_analysis_metadata'].columns['canned_analysis_fk'] == object_id).all()
			object_data['metadata'] = pd.DataFrame([metadata_query_result._asdict() for metadata_query_result in canned_analysis_metadata_query]).set_index('term_name').to_dict()['value']
			object_data['date'] = '{:%B %d, %Y}'.format(object_data['date'])

		# Keywords
		keyword_query = self.session.query(self.tables[self.object_type+'_keyword'].columns['keyword']).filter(self.tables[self.object_type+'_keyword'].columns[self.object_type+'_fk'] == object_id).all()
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
			object_data['fairness']['user_evaluation'] = pd.DataFrame(user_evaluations_query.all()).set_index('question_fk')[['answer', 'comment']].to_dict(orient='index') if len(user_evaluations_query.all()) > 0 else {x:{} for x in question_ids}

			# Add all evaluations
			if all_evaluations_query.all():
				all_evaluations_dataframe = pd.DataFrame(all_evaluations_query.all()).groupby('question_fk').aggregate(lambda x: list(x))#.to_dict(orient='index')
				all_evaluations_dataframe['comment'] = [[y for y in x if y != ''] for x in all_evaluations_dataframe['comment']]
				all_evaluations_dict = all_evaluations_dataframe.to_dict(orient='index')
				all_evaluations = {question_id: {'average_score': np.mean([x == 'yes' for x in all_evaluations_dict[question_id]['answer'] if x]), 'comments': list(set(all_evaluations_dict[question_id]['comment']))} for question_id in question_ids}
				nr_evaluations = max([len(x['user_fk']) for x in all_evaluations_dict.values()])
			else:
				all_evaluations = {x: {} for x in question_ids}
				nr_evaluations = 0
			object_data['fairness']['all_evaluations'] = all_evaluations
			object_data['fairness']['evaluations'] = nr_evaluations

		# Add ID
		object_data['id'] = object_id

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
			'values': [x[0] for x in self.session.query(self.tables[self.object_type+'_keyword'].columns['keyword']).filter(self.tables[self.object_type+'_keyword'].columns[self.object_type+'_fk'].in_(object_ids)).distinct().all()]
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
					'values': [x[0] for x in self.session.query(self.tables[associated_object_type].columns[object_identifiers[associated_object_type]]).join(self.tables['analysis_to_'+associated_object_type]).join(self.tables['canned_analysis']).distinct().filter(self.tables['canned_analysis'].columns['id'].in_(object_ids)).all()]
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
		search_filters = [x for x in search_filters if x['label'] not in ['pert_ids', 'ctrl_ids', 'creeds_id', 'curator', 'chdir_norm', 'pubchem_cid', 'drugbank_id', 'smiles'] and (len(x['values']) > 1 or x['label'] in used_filters+['dataset_accession', 'tool_name'])]

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
		page_sizes = [(x+1)*10 for x in range(min(count/10, 2)+1)] if count > 10 else []
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

	def __init__(self, engine, session, tables, analysis_file, user_id):
		
		# Save query data
		self.engine, self.session, self.tables = engine, session, tables

		# Read analysis file
		canned_analysis_dataframe = self.read_analysis_file(analysis_file)

		# Check if user can upload more analyses
		if self.check_contributions(nr_canned_analyses = len(canned_analysis_dataframe.index), user_id = user_id):

			# Get object IDs
			print 'uploading objects...'
			for object_type in ['dataset', 'tool', 'canned_analysis']:
				canned_analysis_dataframe = self.get_object_ids(canned_analysis_dataframe = canned_analysis_dataframe, object_type = object_type, user_id = user_id)

			# Upload object relationships
			print 'uploading object relationships...'
			self.upload_object_relationships(canned_analysis_dataframe)

			# Upload metadata
			print 'uploading metadata...'
			self.upload_metadata(canned_analysis_dataframe)

			# Upload keywords
			print 'uploading keywords...'
			self.upload_keywords(canned_analysis_dataframe)

		# Else
		else:
			raise ValueError('Over the maximum allowed cap.')

#############################################
########## 2. Read Uploaded File
#############################################

	def read_analysis_file(self, uploaded_file):

		# Read table
		canned_analysis_dataframe = pd.read_table(uploaded_file)

		# Read metadata
		canned_analysis_dataframe['metadata'] = [json.loads(x) for x in canned_analysis_dataframe['metadata']]		

		# Split datasets and tools
		for column in ['dataset_accession', 'tool_name']:
			canned_analysis_dataframe[column] = [x.split(',') for x in canned_analysis_dataframe[column]]
			unstacked_dataframe = canned_analysis_dataframe.set_index('canned_analysis_url')[column].apply(pd.Series).stack().reset_index(level=-1, drop=True).reset_index().rename(columns={0: column})
			canned_analysis_dataframe = canned_analysis_dataframe.drop(column, axis=1).merge(unstacked_dataframe, on='canned_analysis_url', how='inner')

		# Return
		return canned_analysis_dataframe

#############################################
########## 3. Check Contributions
#############################################

	def check_contributions(self, nr_canned_analyses, user_id):

		# Get max number of contributions
		max_contributions = self.session.query(self.tables['user'].columns['max_contributions']).filter(self.tables['user'].columns['id'] == user_id).all()[0][0]

		# Get number of existing contributions
		nr_contributions = len(self.session.query(self.tables['canned_analysis'].columns['id']).join(self.tables['contribution']).filter(self.tables['contribution'].columns['user_fk'] == user_id).all())

		# Return
		return (max_contributions-nr_canned_analyses)>nr_contributions

#############################################
########## 4. Get Object IDs
#############################################

	def get_object_ids(self, canned_analysis_dataframe, object_type, user_id):

		# Get data
		if object_type == 'dataset':
			dataframe_to_upload = canned_analysis_dataframe['dataset_accession'].drop_duplicates().to_frame().set_index('dataset_accession', drop=False)
		elif object_type == 'tool':
			dataframe_to_upload = canned_analysis_dataframe['tool_name'].drop_duplicates().to_frame().set_index('tool_name', drop=False)
		elif object_type == 'canned_analysis':
			dataframe_to_upload = canned_analysis_dataframe[['canned_analysis_title', 'canned_analysis_description', 'canned_analysis_url', 'canned_analysis_preview_url']].drop_duplicates().set_index('canned_analysis_url', drop=False)
			contribution_submission = self.engine.execute(self.tables['contribution'].insert(), {'user_fk': user_id})
			dataframe_to_upload['contribution_fk'] = contribution_submission.inserted_primary_key[0]

		# Insert ignore
		self.engine.execute(self.tables[object_type].insert().prefix_with('IGNORE'), dataframe_to_upload.to_dict(orient='records'))

		# Get IDs dict
		id_query = self.session.query(self.tables[object_type].columns['id'], self.tables[object_type].columns[dataframe_to_upload.index.name]).filter(self.tables[object_type].columns[dataframe_to_upload.index.name].in_(dataframe_to_upload.index.tolist())).all()
		id_dataframe = pd.DataFrame(id_query).rename(columns={'id': object_type+'_fk'})

		# Join
		canned_analysis_dataframe = canned_analysis_dataframe.merge(id_dataframe, on=dataframe_to_upload.index.name, how='inner')

		return canned_analysis_dataframe

#############################################
########## 5. Upload Object Relationships
#############################################

	def upload_object_relationships(self, canned_analysis_dataframe):

		# Upload object relationships
		for object_type in ['dataset', 'tool']:
			self.engine.execute(self.tables['analysis_to_'+object_type].insert().prefix_with('IGNORE'), canned_analysis_dataframe[['canned_analysis_fk', object_type+'_fk']].drop_duplicates().to_dict(orient='records'))

#############################################
########## 6. Upload Metadata
#############################################

	def upload_metadata(self, canned_analysis_dataframe):

		# Initialize metadata dataframe
		metadata_dataframe = pd.DataFrame()

		# Upload terms
		terms = list(set([key for metadata_dict in canned_analysis_dataframe['metadata'] for key in metadata_dict.keys()]))
		self.engine.execute(self.tables['term'].insert().prefix_with('IGNORE'), [{'term_name': x} for x in terms])

		# Get term IDs
		term_dataframe = pd.DataFrame(self.session.query(self.tables['term'].columns['id'], self.tables['term'].columns['term_name']).all()).rename(columns={'id': 'term_fk'})

		# Append metadata
		for index, rowData in canned_analysis_dataframe.iterrows():
			analysis_metadata_dataframe = pd.Series(rowData['metadata']).to_frame().reset_index().rename(columns={'index': 'term_name', 0: 'value'}).merge(term_dataframe, on='term_name', how='left').drop('term_name', axis=1)
			analysis_metadata_dataframe['canned_analysis_fk'] = rowData['canned_analysis_fk']
			metadata_dataframe = pd.concat([metadata_dataframe, analysis_metadata_dataframe.dropna()]).drop_duplicates()

		# Upload
		self.engine.execute(self.tables['canned_analysis_metadata'].insert().prefix_with('IGNORE'), metadata_dataframe.to_dict(orient='records'))

#############################################
########## 7. Upload Keywords
#############################################

	def upload_keywords(self, canned_analysis_dataframe):

		try:
			# Initialize keyword dataframe
			keyword_dataframe = canned_analysis_dataframe.copy()[['canned_analysis_fk', 'keywords']].dropna()
			keyword_dataframe = pd.DataFrame([{'keyword': keyword, 'canned_analysis_fk': rowData['canned_analysis_fk']} for index, rowData in keyword_dataframe.iterrows() for keyword in rowData['keywords'].split(',') if rowData['keywords']]).drop_duplicates()

			# Upload
			self.engine.execute(self.tables['canned_analysis_keyword'].insert().prefix_with('IGNORE'), keyword_dataframe.to_dict(orient='records'))
		except:
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

		# Upload
		upload_string = 'REPLACE INTO {object_type}_evaluation (question_fk, user_fk, {object_type}_fk, answer, comment) VALUES ('.format(**evaluation_info) + '), ('.join([', '.join([rowData[x] if x not in ['comment', 'answer'] else '"'+rowData[x].replace('"', '')+'"' for x in ['question_fk', 'user_fk', evaluation_info['object_type']+'_fk', 'answer', 'comment']]) for index, rowData in score_dataframe.iterrows()]) + ')'
		engine.execute(upload_string)

#############################################
########## 2. Prepare Score Dataframe
#############################################

	def prepare_score_dataframe(self, evaluation_scores, evaluation_info):

		# Convert to dataframe
		melted_score_dataframe = pd.Series(evaluation_scores).rename('answer').to_frame()

		# Add columns
		melted_score_dataframe['question_fk'] = [x.split('-')[2] for x in melted_score_dataframe.index]
		melted_score_dataframe['column_type'] = ['comment' if 'comment' in x else 'answer' for x in melted_score_dataframe.index]

		# Cast
		score_dataframe = pd.pivot_table(melted_score_dataframe, index='question_fk', columns='column_type', values='answer', aggfunc='first').reset_index().replace('None', 'NULL')

		# Add data
		score_dataframe['user_fk'] = evaluation_info['user_id']
		score_dataframe[evaluation_info['object_type']+'_fk'] = evaluation_info['object_id']

		# Return
		return score_dataframe

#################################################################
#################################################################
############### 5. Update Database API ##########################
#################################################################
#################################################################

#############################################
########## 1. Initialization
#############################################

class UpdateDatabase:

	def __init__(self, engine, session, tables, file_directory):

		# Add query data
		self.engine, self.session, self.tables = engine, session, tables

		# Upload tool data
		self.upload_tool_data(file_directory)

		# Upload dataset data
		self.upload_dataset_data(file_directory)

		# Upload canned analysis data
		self.upload_canned_analysis_data(file_directory)

#############################################
########## 2. Upload
#############################################

	def upload_table(self, dataframe, table_name, identifier=None):

		# Fix date
		if 'date' in dataframe.columns:
			dataframe['date'] = [datetime.strptime(x, '%d %B %Y') for x in dataframe['date']]

		# Upload
		self.engine.execute(self.tables[table_name].insert().prefix_with('IGNORE'), dataframe.to_dict(orient='records'))

		# If identifier
		if identifier:

			# Get IDs
			id_dataframe = pd.DataFrame(self.session.query(self.tables[table_name].columns['id'], self.tables[table_name].columns[identifier]).all()).rename(columns={'id': table_name+'_fk'})

			# Return 
			return id_dataframe

#############################################
########## 3. Tool Data
#############################################

	def upload_tool_data(self, file_directory):

		# Read dataframes
		dataframes = {x: pd.read_table(os.path.join(file_directory, x+'.txt')) for x in ['article', 'article_metrics', 'tool', 'related_tool', 'tool_keyword']}

		# Upload tools
		tool_id_dataframe = self.upload_table(dataframe = dataframes['tool'], table_name = 'tool', identifier = 'tool_name')

		# Upload articles
		article_dataframe = dataframes['article'].merge(dataframes['tool'], on='doi').merge(tool_id_dataframe, on='tool_name')[['doi', 'abstract', 'article_title', 'authors', 'date', 'journal_fk', 'tool_fk']]
		article_id_dataframe = self.upload_table(dataframe = article_dataframe, table_name = 'article', identifier = 'doi')

		# Upload article metrics
		article_metrics_dataframe = dataframes['article_metrics'].merge(article_id_dataframe, on='doi').dropna()
		self.upload_table(dataframe = article_metrics_dataframe, table_name = 'article_metrics')

		# Upload keywords
		tool_keyword_dataframe = dataframes['tool_keyword'].merge(tool_id_dataframe, on='tool_name').drop('tool_name', axis=1)
		self.upload_table(dataframe = tool_keyword_dataframe, table_name = 'tool_keyword')

		# Upload related tools
		related_tool_dataframe = dataframes['related_tool'].merge(tool_id_dataframe, left_on='source_tool_name', right_on='tool_name').rename(columns={'tool_fk': 'source_tool_fk'}).merge(tool_id_dataframe, left_on='target_tool_name', right_on='tool_name').rename(columns={'tool_fk': 'target_tool_fk'})[['source_tool_fk', 'target_tool_fk', 'similarity']]
		self.upload_table(dataframe = related_tool_dataframe, table_name = 'related_tool')

#############################################
########## 4. Dataset Data
#############################################

	def upload_dataset_data(self, file_directory):

		# Read dataframes
		dataframes = {x: pd.read_table(os.path.join(file_directory, x+'.txt')) for x in ['dataset', 'related_dataset', 'dataset_keyword', 'related_tool', 'tool_keyword']}

		# Upload datasets
		dataset_id_dataframe = self.upload_table(dataframe = dataframes['dataset'], table_name = 'dataset', identifier = 'dataset_accession')

		# Upload keywords
		dataset_keyword_dataframe = dataframes['dataset_keyword'].merge(dataset_id_dataframe, on='dataset_accession').drop('dataset_accession', axis=1)
		self.upload_table(dataframe = dataset_keyword_dataframe, table_name = 'dataset_keyword')

		# Upload related datasets
		related_dataset_dataframe = dataframes['related_dataset'].merge(dataset_id_dataframe, left_on='source_dataset_accession', right_on='dataset_accession').rename(columns={'dataset_fk': 'source_dataset_fk'}).merge(dataset_id_dataframe, left_on='target_dataset_accession', right_on='dataset_accession').rename(columns={'dataset_fk': 'target_dataset_fk'})[['source_dataset_fk', 'target_dataset_fk', 'similarity']]
		self.upload_table(dataframe = related_dataset_dataframe, table_name = 'related_dataset')


#############################################
########## 5. Canned Analysis Data
#############################################

	def upload_canned_analysis_data(self, file_directory):

		# Read dataframes
		dataframes = {x: pd.read_table(os.path.join(file_directory, x+'.txt')) for x in ['related_canned_analysis']}

		# Read canned analysis ID
		canned_analysis_id_dataframe = pd.DataFrame(self.session.query(self.tables['canned_analysis'].columns['id'], self.tables['canned_analysis'].columns['canned_analysis_accession']).all()).rename(columns={'id': 'canned_analysis_fk'})

		# Upload related canned analyses
		related_canned_analysis_dataframe = dataframes['related_canned_analysis'].merge(canned_analysis_id_dataframe, left_on='source_canned_analysis_accession', right_on='canned_analysis_accession').rename(columns={'canned_analysis_fk': 'source_canned_analysis_fk'}).merge(canned_analysis_id_dataframe, left_on='target_canned_analysis_accession', right_on='canned_analysis_accession').rename(columns={'canned_analysis_fk': 'target_canned_analysis_fk'})[['source_canned_analysis_fk', 'target_canned_analysis_fk', 'similarity']]
		self.upload_table(dataframe = related_canned_analysis_dataframe, table_name = 'related_canned_analysis')

