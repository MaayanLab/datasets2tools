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
from sqlalchemy import or_, and_, asc, func

#################################################################
#################################################################
############### 1. API Wrapper ##################################
#################################################################
#################################################################

#############################################
########## 1. Initialization
#############################################

class Datasets2Tools:

	def __init__(self, engine, session, tables):
		
		# Save engine and tables
		self.engine = engine
		self.session = session
		self.tables = tables

#############################################
########## 2. Search
#############################################

	def search(self, search_options, display_options=None, get_related_objects=False, get_fairness=False, user_id=None):

		# Try
		try:
			search_results = Search(self.engine, self.session, self.tables, search_options, display_options, get_related_objects, get_fairness, user_id)
			self.session.commit()
		except:
			search_results = None
			self.session.rollback()
			raise

		# Return
		return search_results
			
#############################################
########## 3. Upload
#############################################

	def upload(self):

		# Return result
		return ''

#################################################################
#################################################################
############### 2. Search API ###################################
#################################################################
#################################################################

#############################################
########## 1. Initialization
#############################################

class Search:

	def __init__(self, engine, session, tables, search_options, display_options, get_related_objects, get_fairness, user_id):

		# Save query data
		self.engine, self.session, self.tables, self.object_type = engine, session, tables, search_options.pop('object_type')

		# Get IDs
		ids = self.get_ids(search_options)

		# # Filter IDs (sort and get offset)
		# filtered_ids = self.filter_ids(ids=ids, display_options=display_options)

		# # Get search results
		# self.search_results = self.get_object_data(ids = filtered_ids, get_related_objects = get_related_objects, get_fairness = get_fairness, user_id = user_id),
		# self.filter_options = self.get_filter_options(object_ids = object_ids),
		# self.display_options = self.get_display_options(object_ids = object_ids)

#############################################
########## 2. Get IDs
#############################################

	def get_ids(self, search_options):

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
		if 'q' in search_options.keys():
			q = search_options.pop('q')
			if self.object_type == 'dataset':
				query = query.filter(or_(self.tables['dataset'].columns['dataset_accession'].like(q), self.tables['dataset'].columns['dataset_title'].like(q), self.tables['dataset'].columns['dataset_description'].like(q)))
			elif self.object_type == 'tool':
				query = query.filter(or_(self.tables['tool'].columns['tool_name'].like(q), self.tables['tool'].columns['tool_description'].like(q)))
			elif self.object_type == 'canned_analysis':
				query = query.filter(or_(self.tables['canned_analysis'].columns['canned_analysis_accession'].like(q), self.tables['canned_analysis'].columns['canned_analysis_title'].like(q), self.tables['canned_analysis'].columns['canned_analysis_description'].like(q), self.tables['dataset'].columns['dataset_accession'].like(q), self.tables['tool'].columns['tool_name'].like(q)))

		# Keyword search
		if 'keyword' in search_options.keys():
			keyword = search_options.pop('keyword')
			query = query.filter(self.tables[self.object_type].columns['id'].in_(self.session.query(self.tables['keyword'].columns[self.object_type+'_fk']).distinct().filter(self.tables['keyword'].columns['keyword'] == keyword).subquery()))

		# Dataset search
		if 'dataset_accession' in search_options.keys():
			dataset_accession = search_options.pop('dataset_accession')
			query = query.filter(self.tables['dataset'].columns['dataset_accession'] == dataset_accession)

		# Tool search
		if 'tool_name' in search_options.keys():
			tool_name = search_options.pop('tool_name')
			query = query.filter(self.tables['tool'].columns['tool_name'] == tool_name)

		# Canned analysis search
		if 'canned_analysis_accession' in search_options.keys():
			canned_analysis_accession = search_options.pop('canned_analysis_accession')
			query = query.filter(self.tables['canned_analysis'].columns['canned_analysis_accession'] == canned_analysis_accession)

		# Metadata search
		if self.object_type == 'canned_analysis' and len(search_options.keys()) > 0:
			for term_name, value in search_options.iteritems():
				query = query.filter(tables['canned_analysis'].columns['id'].in_(session.query(tables['canned_analysis_metadata'].columns['canned_analysis_fk']).distinct() .join(tables['term']).filter(and_(tables['term'].columns['term_name'] == term_name, tables['canned_analysis_metadata'].columns['value'] == value)).subquery()))

		# Get query
		print query
		return query


		# if self.object_type == 'dataset':
		# elif self.object_type == 'tool':
		# elif self.object_type == 'canned_analysis':

