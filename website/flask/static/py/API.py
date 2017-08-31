import json
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, MetaData

def upload_and_get_ids(dataframe_to_upload, table_name, engine, identifiers={'tool': 'tool_name', 'dataset': 'dataset_accession', 'canned_analysis': 'canned_analysis_url', 'article': 'doi', 'term': 'term_name'}):

    # Get table object
    table = Table(table_name, MetaData(), autoload=True, autoload_with=engine)

    # Insert data
    engine.execute(table.insert().prefix_with('IGNORE'), dataframe_to_upload.to_dict(orient='records'))

    # Get data
    table_data = engine.execute(table.select())

    # Get identifier column
    identifier_column = identifiers[table_name]

    # Convert to dataframe
    result_dataframe = pd.DataFrame(table_data.fetchall(), columns=table_data.keys())[['id', identifier_column]]

    # Merge IDs
    id_dataframe = dataframe_to_upload.merge(result_dataframe, on=identifier_column, how='left')[['id', identifier_column]].rename(columns={'id': table_name+'_fk'})

    # Return
    return id_dataframe

def upload_analyses(canned_analysis_dataframe, engine, session):

	# Load metadata JSON
	canned_analysis_dataframe['metadata'] = [json.loads(x) for x in canned_analysis_dataframe['metadata']]

	# Get dataset, tool and canned analysis dataframes to upload
	dataframes_to_upload = {
	    'dataset': canned_analysis_dataframe['dataset_accession'].to_frame().drop_duplicates(),
	    'tool': canned_analysis_dataframe['tool_name'].to_frame().drop_duplicates(),
	    'canned_analysis': canned_analysis_dataframe.drop(['dataset_accession', 'tool_name', 'metadata'], axis=1),
	    'term': pd.Series(list(set([keys for metadata_dict in canned_analysis_dataframe['metadata'] for keys in metadata_dict.keys() for term_name in keys]))).rename('term_name').to_frame()
	}

	# Upload dataframes and get IDs
	id_data = {object_type: upload_and_get_ids(dataframe_to_upload, object_type, engine) for object_type, dataframe_to_upload in dataframes_to_upload.iteritems()}

	# Add foreign keys
	fk_conversion_dataframe = canned_analysis_dataframe.merge(id_data['canned_analysis'], on='canned_analysis_url', how='left').merge(id_data['tool'], on='tool_name', how='left').merge(id_data['dataset'], on='dataset_accession', how='left')[['dataset_fk', 'tool_fk', 'canned_analysis_fk', 'metadata']]

	# Upload dataset and tool matching
	for object_type in ['dataset', 'tool']:
	    
	    # Get table object
	    table = Table(object_type, MetaData(), autoload=True, autoload_with=engine)
	    
	    # Upload
	    engine.execute(table.insert().prefix_with('IGNORE'), fk_conversion_dataframe[['canned_analysis_fk', object_type+'_fk']].to_dict(orient='records'))

	# Initialize metadata dataframe
	metadata_dataframe_ready_to_upload = pd.DataFrame()

	# Loop through canned analysis dataframe to get metadata
	for index, rowData in fk_conversion_dataframe.iterrows():
	    
	    # Get metadata dataframe
	    metadata_dataframe = pd.Series(rowData['metadata']).to_frame().reset_index().rename(columns={'index': 'term_name', 0: 'value'}).merge(id_data['term'], on='term_name', how='left').drop('term_name', axis=1)

	    # Add canned analysis foreign key
	    metadata_dataframe['canned_analysis_fk'] = rowData['canned_analysis_fk']
	    
	    # Concantenate
	    metadata_dataframe_ready_to_upload = pd.concat([metadata_dataframe_ready_to_upload, metadata_dataframe])

	# Get table object
	canned_analysis_metadata = Table('canned_analysis_metadata', MetaData(), autoload=True, autoload_with=engine)

	# Upload
	engine.execute(canned_analysis_metadata.insert().prefix_with('IGNORE'), metadata_dataframe_ready_to_upload.to_dict(orient='records'))

	# Return
	upload_results = json.dumps(canned_analysis_dataframe.merge(id_data['canned_analysis'], on='canned_analysis_url').rename(columns={'canned_analysis_fk': 'id'}).to_dict(orient='records'))

	# Commit
	session.commit()

	# Return results
	return upload_results