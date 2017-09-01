import json
import pandas as pd
from sqlalchemy.orm import sessionmaker

query = {'q': '', 'dataset_accession': '', 'tool_name': '', }

def process_query(query_dict, object_type, session, metadata):

	# Dataset
	if object_type == 'dataset':

		# By accession
		if 'dataset_accession' in query_dict.keys():
			query = session.query(metadata.tables[object_type].columns['id']).filter(metadata.tables[object_type].columns['tool_name']==query_dict['dataset_accession'])

	# Tool
	elif object_type == 'tool':

		# By name
		if 'tool_name' in query_dict.keys():
			query = session.query(metadata.tables[object_type].columns['id']).filter(metadata.tables[object_type].columns['tool_name']==query_dict['tool_name'])

	# Get ID list
	ids = [x[0] for x in query.all()]

	# Return ids
	return ids


def get_object_data(object_id, object_type, session, metadata):

	# Dataset
	if object_type == 'dataset':
		pass

	elif object_type == 'tool':
		
		# Perform tool query
		tool_query = session.query(metadata.tables[object_type]).filter(metadata.tables[object_type].columns['id'] == object_id)

		# Get tool data
		object_data = {key: value for key, value in zip(metadata.tables[object_type].columns.keys(), tool_query.all()[0])}

		# Perform article query
		article_query = session.query(metadata.tables['article']).filter(metadata.tables['article'].columns['tool_fk'] == object_id)

		# Get article data
		object_data['articles'] = [{key: value if key != 'abstract' else json.loads(value) for key, value in zip(metadata.tables['article'].columns.keys(), query_result)} for query_result in article_query.all()]

	elif object_type == 'canned_analysis':
		pass

	# Return
	return object_data


def search_database(query, object_type, session, metadata):

	# Get IDs
	ids = process_query(query, object_type, session, metadata)

	# Get object data
	search_results = [get_object_data(x, object_type, session, metadata) for x in ids]

	# Flatten list
	search_results = search_results[0] if len(search_results) == 1 else search_results

	# Return
	return search_results

def get_related_objects(object_id, object_type, session, metadata):

	# Perform related object query
	related_object_query = session.query(metadata.tables['related_'+object_type].columns['_'.join(['target', object_type,'fk'])]).filter(metadata.tables['related_'+object_type].columns['_'.join(['source', object_type,'fk'])] == object_id)

	# Get ids
	print related_object_query.all()
	related_object_data = [get_object_data(x[0], object_type, session, metadata) for x in related_object_query.all()]

	# Return
	return related_object_data

