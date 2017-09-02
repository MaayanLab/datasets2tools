import json
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_, and_

def process_query(query_dict, search_options_dict, session, metadata):

	# Get object type
	object_type = search_options_dict['object_type']

	# Initialize query object
	query = session.query(metadata.tables[object_type].columns['id']).distinct()

	# Check if object is dataset or tool
	if object_type == 'dataset' or object_type == 'tool':

		# Get other object
		other_object_type = 'dataset' if object_type == 'tool' else 'tool'

		# Join canned analyses
		query = query.join(metadata.tables['analysis_to_'+object_type]) \
					 .join(metadata.tables['canned_analysis']) \
					 .join(metadata.tables['analysis_to_'+other_object_type]) \
					 .join(metadata.tables[other_object_type])

		# Perform regular query
		for query_key, query_value in query_dict.iteritems():

			# Dataset and tool search 
			if query_key in ['dataset_accession', 'tool_name']:

				# Simple search
				if query_key.split('_')[0] == object_type:
					query = query.filter(metadata.tables[object_type].columns[query_key] == query_value)
				# Cross search
				else:
					query = query.filter(metadata.tables[query_key.split('_')[0]].columns[query_key] == query_value)

			# Canned analysis search
			if query_key == 'canned_analysis_fk':

				# Filter by canned analysis
				query = query.filter(metadata.tables['canned_analysis'].columns['id'] == query_dict.pop('canned_analysis_fk'))

		# Dataset cases
		if object_type == 'dataset':

			# Dataset text search
			if 'q' in query_dict.keys():

				# Get query
				q = '%'+query_dict.pop('q')+'%'

				# Perform text search
				query = query.filter(or_(metadata.tables['dataset'].columns['dataset_title'].like(q),
										 metadata.tables['dataset'].columns['dataset_description'].like(q),
										 metadata.tables['dataset'].columns['dataset_accession'].like(q)))

			# Sort

		# Tool cases
		if object_type == 'tool':

			# Tool text search
			if 'q' in query_dict.keys():

				# Get query
				q = '%'+query_dict.pop('q')+'%'

				# Perform text search
				query = query.filter(or_(metadata.tables['tool'].columns['tool_name'].like(q),
										 metadata.tables['tool'].columns['tool_description'].like(q)))

			# Sort

	# Canned Analysis
	elif object_type == 'canned_analysis':

		# Expand query by adding tools and datasets
		query = query.join(metadata.tables['analysis_to_dataset']) \
					 .join(metadata.tables['analysis_to_tool']) \
					 .join(metadata.tables['dataset']) \
					 .join(metadata.tables['repository']) \
					 .join(metadata.tables['tool'])

		# Check if dataset has been specified
		if 'dataset_accession' in query_dict.keys():

			# Filter by dataset
			query = query.filter(metadata.tables['dataset'].columns['dataset_accession'] == query_dict.pop('dataset_accession'))

		# Check if tool has been specified
		if 'tool_name' in query_dict.keys():

			# Filter by dataset
			query = query.filter(metadata.tables['tool'].columns['tool_name'] == query_dict.pop('tool_name'))

		# Canned analysis text search
		if 'q' in query_dict.keys():

			# Get query
			q = '%'+query_dict.pop('q')+'%'

			# Perform text search
			query = query.filter(or_(metadata.tables['canned_analysis'].columns['canned_analysis_title'].like(q),
									 metadata.tables['dataset'].columns['dataset_accession'].like(q),
									 metadata.tables['tool'].columns['tool_name'].like(q),
									 metadata.tables['canned_analysis'].columns['canned_analysis_description'].like(q)))

		# All terms left should be metadata
		if len(query_dict) > 0:

			# Expand query with metadata
			query = query.join(metadata.tables['canned_analysis_metadata']) \
						 .join(metadata.tables['term'])

			# Loop through metadata keys and values
			for term_name, value in query_dict.iteritems():

				# Perform metadata query
				query = query.filter(and_(metadata.tables['term'].columns['term_name'] == term_name,
										  metadata.tables['canned_analysis_metadata'].columns['value'] == value))

		# Sort


	# Get ID list
	ids = [x[0] for x in query.all()]

	# Return ids
	return ids


def get_object_data(object_id, object_type, session, metadata, get_related):

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
	if get_related:

		# Perform related object query
		related_object_query = session.query(metadata.tables['related_'+object_type].columns['_'.join(['target', object_type,'fk'])]) \
									  .filter(metadata.tables['related_'+object_type].columns['_'.join(['source', object_type,'fk'])] == object_id)

		# Get ids
		object_data['related_objects'] = [get_object_data(x[0], object_type, session, metadata, get_related=False) for x in related_object_query.all()]

	# Return
	return object_data

def search_database(query_dict, search_options_dict, session, metadata, get_related=False):

	# Get IDs
	ids = process_query(query_dict, search_options_dict, session, metadata)

	# Get object data
	search_results = [get_object_data(x, search_options_dict['object_type'], session, metadata, get_related) for x in ids]

	# Return
	return search_results
