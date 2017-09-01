import json
import pandas as pd
from sqlalchemy.orm import sessionmaker

query = {'q': '', 'dataset_accession': '', 'tool_name': '', }

def process_query(query_dict, object_type, session, metadata):

	# Initialize query object
	query = session.query(metadata.tables[object_type].columns['id']).distinct()

	# Dataset
	if object_type == 'dataset' or object_type == 'tool':

		# Check if canned analysis in query
		if 'canned_analysis_fk' in query_dict.keys():

			# Expand query and filter by canned analysis
			query = query.join(metadata.tables['analysis_to_'+object_type]).filter(metadata.tables['analysis_to_'+object_type].columns['canned_analysis_fk'] == query_dict.pop('canned_analysis_fk'))

		# Dataset cross-search (search datasets analyzed by tool)
		if object_type == 'dataset' and 'tool_name' in query_dict.keys():

			# Expand query and filter by tool
			query = query.join(metadata.tables['analysis_to_dataset']) \
						 .join(metadata.tables['canned_analysis']) \
						 .join(metadata.tables['analysis_to_tool']) \
						 .join(metadata.tables['tool']) \
						 .filter(metadata.tables['tool'].columns['tool_name'] == query_dict.pop('tool_name'))

		# Tool cross-search (search tools with analyses of dataset)
		if object_type == 'tool' and 'dataset_accession' in query_dict.keys():

			# Expand query and filter by tool
			query = query.join(metadata.tables['analysis_to_tool']) \
						 .join(metadata.tables['canned_analysis']) \
						 .join(metadata.tables['analysis_to_dataset']) \
						 .join(metadata.tables['dataset']) \
						 .filter(metadata.tables['dataset'].columns['dataset_accession'] == query_dict.pop('dataset_accession'))

		# Check if regular queries
		if len(query_dict) > 0:

			# Perform regular query
			for query_key, query_value in query_dict.iteritems():

				# Add query
				query = query.filter(metadata.tables[object_type].columns[query_key] == query_value)

	# Canned Analysis
	elif object_type == 'canned_analysis':

		# Expand query by adding tools and datasets
		query = query.join(metadata.tables['analysis_to_dataset']) \
					 .join(metadata.tables['analysis_to_tool']) \
					 .join(metadata.tables['dataset']) \
					 .join(metadata.tables['tool'])

		# Check if dataset
		if 'dataset_accession' in query_dict.keys():

			# Filter by dataset
			query = query.filter(metadata.tables['dataset'].columns['dataset_accession'] == query_dict.pop('dataset_accession'))

		# Check if tool
		if 'tool_name' in query_dict.keys():

			# Filter by dataset
			query = query.filter(metadata.tables['tool'].columns['tool_name'] == query_dict.pop('tool_name'))

		# If text search
		if 'q' in query_dict.keys():

			# Perform text search
			pass

		# All terms left should be metadata
		if len(query_dict) > 0:

			# Perform metadata query
			pass

	# Get ID list
	ids = [x[0] for x in query.all()]

	print object_type
	print ids

	# Return ids
	return ids


def get_object_data(object_id, object_type, session, metadata, get_related=False):

	# Dataset
	if object_type == 'dataset':
		
		# Perform dataset query
		dataset_query = session.query(metadata.tables['dataset'], metadata.tables['repository']).join(metadata.tables['repository']).filter(metadata.tables['dataset'].columns['id'] == object_id).all()

		# Get tool data
		object_data = [x._asdict() for x in dataset_query][0]

	# Tool
	elif object_type == 'tool':
		
		# Perform tool query
		tool_query = session.query(metadata.tables['tool']).filter(metadata.tables['tool'].columns['id'] == object_id)

		# Get tool data
		object_data = {key: value for key, value in zip(metadata.tables[object_type].columns.keys(), tool_query.all()[0])}

		# Perform article query
		article_query = session.query(metadata.tables['article'], metadata.tables['journal']).join(metadata.tables['journal']).filter(metadata.tables['article'].columns['tool_fk'] == object_id).all()

		# Get article data
		object_data['articles'] = [x._asdict() for x in article_query]

		# Loop through articles
		for i in range(len(object_data['articles'])):

			# Convert to dict
			object_data['articles'][i]['abstract'] = json.loads(object_data['articles'][i]['abstract'])

	# Canned Analysis
	elif object_type == 'canned_analysis':
				
		# Perform analysis query
		canned_analysis_query = session.query(metadata.tables['canned_analysis']).filter(metadata.tables['canned_analysis'].columns['id'] == object_id).all()

		# Get tool data
		object_data = [x._asdict() for x in canned_analysis_query][0]

	# Perform keyword query
	keyword_query = session.query(metadata.tables['keyword'].columns['keyword']).filter(metadata.tables['keyword'].columns[object_type+'_fk'] == object_id).all()
	
	# Get keyword data
	object_data['keywords'] = [x[0] for x in keyword_query]

	# Get related objects
	if get_related:

		# Perform related object query
		related_object_query = session.query(metadata.tables['related_'+object_type].columns['_'.join(['target', object_type,'fk'])]).filter(metadata.tables['related_'+object_type].columns['_'.join(['source', object_type,'fk'])] == object_id)

		# Get ids
		object_data['related_objects'] = [get_object_data(x[0], object_type, session, metadata, get_related=False) for x in related_object_query.all()]

	# Return
	return object_data

def search_database(query, object_type, session, metadata, get_related=True):

	# Get IDs
	ids = process_query(query, object_type, session, metadata)

	# Get object data
	search_results = [get_object_data(x, object_type, session, metadata) for x in ids]

	# Return
	return search_results
