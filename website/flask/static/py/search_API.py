#################################################################
#################################################################
############### Datasets2Tools Search API #######################
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

##### 2. Database modules #####
from sqlalchemy import or_, and_

#################################################################
#################################################################
############### 2. Search Functions #############################
#################################################################
#################################################################

#############################################
########## 1. Process Query
#############################################

def process_query(input_search_options, object_type, session, metadata):

	# Initialize query object
	query = session.query(metadata.tables[object_type].columns['id']).distinct()

	# Get keywords
	keyword_dict = input_search_options.pop('keyword') if 'keyword' in input_search_options.keys() else None

	# Check if object is dataset or tool
	if object_type == 'dataset' or object_type == 'tool':

		# Get other object type
		other_object_type = 'dataset' if object_type == 'tool' else 'tool'

		# Expand query
		query = query.join(metadata.tables['analysis_to_'+object_type]) \
					 .join(metadata.tables['canned_analysis']) \
					 .join(metadata.tables['analysis_to_'+other_object_type]) \
					 .join(metadata.tables[other_object_type])

		# Dataset cases
		if object_type == 'dataset':

			# Dataset text search
			if 'q' in input_search_options.keys():

				# Get query
				q = '%'+input_search_options.pop('q')+'%'

				# Perform text search
				query = query.filter(or_(metadata.tables['dataset'].columns['dataset_accession'].like(q),
										 metadata.tables['dataset'].columns['dataset_title'].like(q),
										 metadata.tables['dataset'].columns['dataset_description'].like(q)))

		# Tool cases
		if object_type == 'tool':

			# Tool text search
			if 'q' in input_search_options.keys():

				# Get query
				q = '%'+input_search_options.pop('q')+'%'

				# Perform text search
				query = query.filter(or_(metadata.tables['tool'].columns['tool_name'].like(q),
										 metadata.tables['tool'].columns['tool_description'].like(q)))

		# Perform regular query
		for query_key, query_value in input_search_options.iteritems():

			# Check if cross-search
			if object_type in query_key:

				# Normal search
				query = query.filter(metadata.tables[object_type].columns[query_key] == query_value)

			else:

				# Cross-search
				query = query.filter(metadata.tables[other_object_type].columns[query_key] == query_value)

	# Canned Analysis
	elif object_type == 'canned_analysis':

		# Expand query by adding tools and datasets
		query = query.join(metadata.tables['analysis_to_dataset']) \
					 .join(metadata.tables['analysis_to_tool']) \
					 .join(metadata.tables['dataset']) \
					 .join(metadata.tables['repository']) \
					 .join(metadata.tables['tool'])

		# Check if dataset has been specified
		if 'dataset_accession' in input_search_options.keys():

			# Filter by dataset
			query = query.filter(metadata.tables['dataset'].columns['dataset_accession'] == input_search_options.pop('dataset_accession'))

		# Check if tool has been specified
		if 'tool_name' in input_search_options.keys():

			# Filter by dataset
			query = query.filter(metadata.tables['tool'].columns['tool_name'] == input_search_options.pop('tool_name'))

		# Canned analysis text search
		if 'q' in input_search_options.keys():

			# Get query
			q = '%'+input_search_options.pop('q')+'%'

			# Perform text search
			query = query.filter(or_(metadata.tables['canned_analysis'].columns['canned_analysis_title'].like(q),
									 metadata.tables['dataset'].columns['dataset_accession'].like(q),
									 metadata.tables['tool'].columns['tool_name'].like(q),
									 metadata.tables['canned_analysis'].columns['canned_analysis_description'].like(q)))

		# All terms left should be metadata
		if len(input_search_options) > 0:

			# Expand query with metadata
			query = query.join(metadata.tables['canned_analysis_metadata']) \
						 .join(metadata.tables['term'])

			# Loop through metadata keys and values
			for term_name, value in input_search_options.iteritems():

				# Perform metadata query
				query = query.filter(and_(metadata.tables['term'].columns['term_name'] == term_name,
										  metadata.tables['canned_analysis_metadata'].columns['value'] == value))

	# Get ID list
	ids = [x[0] for x in query.all()]

	# Return ids
	return ids

#############################################
########## 2. Get Object Data
#############################################

def get_object_data(object_id, object_type, session, metadata, landing_page):

	# Dataset
	if object_type == 'dataset':
		
		# Perform dataset query
		dataset_query = session.query(metadata.tables['dataset'], metadata.tables['repository']) \
							   .join(metadata.tables['repository']) \
							   .filter(metadata.tables['dataset'].columns['id'] == object_id).all()

		# Get tool data
		object_data = [x._asdict() for x in dataset_query][0]

	# Tool
	elif object_type == 'tool':
		
		# Perform tool query
		tool_query = session.query(metadata.tables['tool']) \
							.filter(metadata.tables['tool'].columns['id'] == object_id)

		# Get tool data
		object_data = {key: value for key, value in zip(metadata.tables[object_type].columns.keys(), tool_query.all()[0])}

		# Perform article query
		article_query = session.query(metadata.tables['article'], metadata.tables['journal']) \
							   .join(metadata.tables['journal']) \
							   .filter(metadata.tables['article'].columns['tool_fk'] == object_id).all()

		# Get article data
		object_data['articles'] = [x._asdict() for x in article_query]

		# Loop through articles
		for i in range(len(object_data['articles'])):

			# Convert to dict
			object_data['articles'][i]['abstract'] = json.loads(object_data['articles'][i]['abstract'])

	# Canned Analysis
	elif object_type == 'canned_analysis':
				
		# Perform analysis query
		canned_analysis_query = session.query(metadata.tables['canned_analysis'], metadata.tables['tool'], metadata.tables['dataset'], metadata.tables['repository']) \
										.join(metadata.tables['analysis_to_tool']) \
										.join(metadata.tables['tool']) \
										.join(metadata.tables['analysis_to_dataset']) \
										.join(metadata.tables['dataset']) \
										.join(metadata.tables['repository']) \
									    .filter(metadata.tables['canned_analysis'].columns['id'] == object_id).all()

		# Perform metadata query
		canned_analysis_metadata_query = session.query(metadata.tables['canned_analysis_metadata'].columns['value'], metadata.tables['term'].columns['term_name']) \
												.join(metadata.tables['term']) \
												.filter(metadata.tables['canned_analysis_metadata'].columns['canned_analysis_fk'] == object_id).all()

		# Get canned analysis data
		object_data = [x._asdict() for x in canned_analysis_query][0]

		# Get metadata
		object_data['metadata'] = pd.DataFrame([metadata_query_result._asdict() for metadata_query_result in canned_analysis_metadata_query]).set_index('term_name').to_dict()['value']

	# Perform keyword query
	keyword_query = session.query(metadata.tables['keyword'].columns['keyword']) \
						   .filter(metadata.tables['keyword'].columns[object_type+'_fk'] == object_id).all()
	
	# Get keyword data
	object_data['keywords'] = [x[0] for x in keyword_query]

	# Get related objects
	if landing_page:

		# Get related object IDs
		related_object_query = session.query(metadata.tables['related_'+object_type].columns['_'.join(['target', object_type,'fk'])]) \
									  .filter(metadata.tables['related_'+object_type].columns['_'.join(['source', object_type,'fk'])] == object_id)

		# Get related object data
		object_data['related_objects'] = [get_object_data(x[0], object_type, session, metadata, landing_page=False) for x in related_object_query.all()]

		# Get FAIRness

	# Return
	return object_data

#############################################
########## 3. Get and Apply Display Options
#############################################

def get_and_apply_display_options(ids, input_display_options, object_type, session, metadata):

	# Initialize query object
	query = session.query(metadata.tables[object_type].columns['id']).distinct()

	# Dataset
	if object_type == 'dataset':
		sorted_ids = ids

	# Tool
	elif object_type == 'tool':
		sorted_ids = ids

	# Canned analysis
	elif object_type == 'canned_analysis':
		sorted_ids = ids

	# Get subset based on offset and page number
	sorted_ids_subset = sorted_ids[(input_display_options['offset']-1)*input_display_options['page_size']: (input_display_options['offset'])*input_display_options['page_size']]

	# Get offsets
	offsets = range(1, len(ids)/input_display_options['page_size']+1)

	# Display options
	output_display_options = {
		'count': len(ids),
		'offset': {'values': offsets, 'selected': input_display_options['offset']},
		'page_size': {'values': [5,10,30], 'selected': input_display_options['page_size']},
		'sort_by': {'values': ['relevance','fairness','date'], 'selected': input_display_options['sort_by']}
	}

	# Return result
	return sorted_ids_subset, output_display_options

#############################################
########## 4. Get Search Options
#############################################

def get_search_options(ids, object_type, input_display_options, session, metadata):

	# Search options
	output_search_options = [{
			'keyword': {'values': ['a','b','c'], 'selected': 'a'}
		}]

	return output_search_options

#################################################################
#################################################################
############### 3. Search Wrappers ##############################
#################################################################
#################################################################

#############################################
########## 1. Search Database
#############################################

def search_database(input_search_options, input_display_options, object_type, session, metadata):

	# Get IDs
	ids = process_query(input_search_options, object_type, session, metadata)

	# Get search options
	output_search_options = get_search_options(ids, object_type, input_display_options, session, metadata)

	# Apply display options
	filtered_ids, output_display_options = get_and_apply_display_options(ids, input_display_options, object_type, session, metadata)

	# Get object data
	search_results = [get_object_data(x, object_type, session, metadata, landing_page=False) for x in filtered_ids]

	# Create search data
	search_data = {'search_results': search_results, 'search_options': output_search_options, 'display_options': output_display_options}

	# Close session
	session.close()

	# Return
	return search_data

#############################################
########## 2. Get Landing Data
#############################################

def get_landing_data(object_identifier, object_type, session, metadata):

	# Get identifier column
	if object_type == 'dataset':
		identifier_column = 'dataset_accession'
	elif object_type == 'tool':
		identifier_column = 'tool_name'
	elif object_type == 'canned_analysis':
		identifier_column = 'canned_analysis_accession'

	# Get search options
	input_search_options = {identifier_column: object_identifier}

	# Get object ID
	object_id = process_query(input_search_options, object_type, session, metadata)[0]

	# Get object data
	object_data = get_object_data(object_id, object_type, session, metadata, landing_page = True)

	# Close session
	session.close()

	# Return object data
	return object_data
