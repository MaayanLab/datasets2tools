#################################################################
#################################################################
############### Canned Analyses ################
#################################################################
#################################################################
##### Author: Denis Torre
##### Affiliation: Ma'ayan Laboratory,
##### Icahn School of Medicine at Mount Sinai

#############################################
########## 1. Load libraries
#############################################
##### 1. Python modules #####
from ruffus import *
import sys, os, glob, json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, MetaData

##### 2. Custom modules #####
# Pipeline running
sys.path.append('pipeline')
import PipelineDatasets2ToolsUpdater as P

#############################################
########## 2. General Setup
#############################################
##### 1. Variables #####
# Spiders
spiders = ['oxford', 'bmc_bioinformatics']

# Database engine
dbFile = '../db.txt'
if os.path.exists(dbFile):
	with open(dbFile) as openfile: database_uri = openfile.readlines()[0]
engine = create_engine(database_uri)

##### 2. R Connection #####

#################################################################
#################################################################
############### 1. Computational Tools ##########################
#################################################################
#################################################################

#######################################################
#######################################################
########## S1. Spiders
#######################################################
#######################################################

#############################################
########## 1. Run Spiders
#############################################

def spiderJobs():
	for spider in spiders:
		yield [None, spider]

@files(spiderJobs)

def runSpiders(infile, outfile):

	# Change directory
	os.chdir('pipeline/scrapy')
	
	# Run
	os.system('scrapy crawl '+outfile)

	# Move back
	os.chdir('../..')

#############################################
########## 2. Extract Tools
#############################################

# @follows(runSpiders)

@follows(mkdir('02-tools'))

@transform(glob.glob('01-journals/*/*.json'),
		  regex(r'01-journals/(.*)/(.*).json'),
		  r'02-tools/\1/\2_tools.txt')

def getTools(infile, outfile):

	# Initialize dataframe
	tool_dataframe = pd.DataFrame()

	# Get dataframe
	with open(infile, 'r') as openfile:

		# Get dataframe
		tool_dataframe = pd.DataFrame(json.loads(openfile.read())['article_data'])[['article_title', 'links', 'doi']]
		
		# Drop no links
		tool_dataframe.drop([index for index, rowData in tool_dataframe.iterrows() if len(rowData['links']) == 0], inplace=True)
		
		# Add link column
		tool_dataframe['tool_homepage_url'] = [x[0] for x in tool_dataframe['links']]

		# Drop links columns
		tool_dataframe.drop('links', inplace=True, axis=1)
		
		# Add tool name column
		tool_dataframe['tool_name'] = [x.split(':')[0].replace('"', '') if ':' in x and len(x.split(':')[0]) < 50 else None for x in tool_dataframe['article_title']]

		# Drop rows with no names
		tool_dataframe.drop([index for index, rowData in tool_dataframe.iterrows() if not rowData['tool_name']], inplace=True)

		# Add tool description
		tool_dataframe['tool_description'] = [x.split(':', 1)[-1].strip() for x in tool_dataframe['article_title']]
		tool_dataframe['tool_description'] = [x[0].upper()+x[1:] for x in tool_dataframe['tool_description']]
		
		# Drop article title
		tool_dataframe.drop('article_title', inplace=True, axis=1)
		
	# Check if tool link works
	indices_to_drop = []

	# Loop through indicies
	for index, rowData in tool_dataframe.iterrows():

		# Try to connect
		try:
			# Check URL
			if 'http' in rowData['tool_homepage_url']: #urllib2.urlopen(rowData['tool_homepage_url']).getcode() in (200, 401)
				pass
			else:
				# Append
				indices_to_drop.append(index)
		except:
				# Append
				indices_to_drop.append(index)

	# Drop
	tool_dataframe.drop(indices_to_drop, inplace=True)

	# Write
	tool_dataframe.to_csv(outfile, sep='\t', index=False, encoding='utf-8')

#############################################
########## 3. Extract Articles
#############################################

@follows(getTools)

@follows(mkdir('03-articles'))

@transform(glob.glob('01-journals/*/*.json'),
		  regex(r'01-journals/(.*)/(.*).json'),
		  add_inputs(r'02-tools/\1/\2_tools.txt'),
		  r'03-articles/\1/\2_articles.txt')

def getArticles(infiles, outfile):

	# Split infiles
	jsonFile, toolFile = infiles

	# Get dataframe
	with open(jsonFile, 'r') as openfile:

		# Get dataframe
		article_dataframe = pd.DataFrame(json.loads(openfile.read())['article_data']).drop('links', axis=1)
		
		# Join authors
		article_dataframe['authors'] = ['; '.join(x) for x in article_dataframe['authors']]
		
		# Fix abstract
		article_dataframe['abstract'] = [json.dumps({'abstract': x}) for x in article_dataframe['abstract']]
		
	# Get tool DOIs
	toolDois = pd.read_table(toolFile)['doi'].tolist()

	# Intersect
	article_dataframe = article_dataframe.set_index('doi').loc[toolDois].reset_index()

	# Get Journal FK dict
	journal_fks = {'bioinformatics': 1, 'database': 2, 'nar': 3, 'bmc-bioinformatics': 4}

	# Add journal fk
	article_dataframe['journal_fk'] = journal_fks[os.path.basename(outfile).split('_')[0]]

	# Write
	article_dataframe.to_csv(outfile, sep='\t', index=False, encoding='utf-8')

#######################################################
#######################################################
########## S2. Prepare Tables
#######################################################
#######################################################

#############################################
########## 1. Tool Table
#############################################

@follows(mkdir('results'))

@merge(getTools,
	   'results/tool.txt')

def prepareToolTable(infiles, outfile):

	# Get dataframe
	tool_dataframe = pd.concat([pd.read_table(x) for x in infiles])

	# Write to outfile
	tool_dataframe.to_csv(outfile, sep='\t', index=False)

#############################################
########## 2. Article Table
#############################################

@merge(getArticles,
	   'results/article.txt')

def prepareArticleTable(infiles, outfile):

	# Get dataframe
	article_dataframe = pd.concat([pd.read_table(x) for x in infiles])

	# Write to outfile
	article_dataframe.to_csv(outfile, sep='\t', index=False)

#############################################
########## 3. Tool Similarity
#############################################

@transform(prepareToolTable,
		   regex(r'(.*)/(.*).txt'),
		   add_inputs(prepareArticleTable),
		   r'\1/related_\2.txt')

def getRelatedTools(infiles, outfile):

	# Split infiles
	toolFile, articleFile = infiles

	# Initialize dataframe
	abstract_dataframe = pd.read_table(articleFile)[['abstract', 'doi']]

	# Fix abstract
	abstract_dataframe['abstract'] = [' '.join([abstract_tuple[1] for abstract_tuple in json.loads(x)['abstract'] if abstract_tuple[0] and abstract_tuple[0].lower() not in [u'contact:', u'availability and implementation', u'supplementary information']]) for x in abstract_dataframe['abstract']]

	# Process abstracts
	processed_abstracts = [P.process_text(x) for x in abstract_dataframe['abstract']]

	# Get similarity and keywords
	article_similarity_dataframe, article_keyword_dataframe = P.extract_text_similarity_and_keywords(processed_abstracts, labels=abstract_dataframe['doi'])

	# Get tool-doi correspondence
	tool_dois = pd.read_table(toolFile).set_index('doi')['tool_name'].to_dict()

	# Rename similarity
	tool_similarity_dataframe = article_similarity_dataframe.loc[tool_dois.keys(), tool_dois.keys()].rename(index=tool_dois, columns=tool_dois)

	# Fill diagonal
	np.fill_diagonal(tool_similarity_dataframe.values, np.nan)

	# Melt tool similarity
	melted_tool_similarity_dataframe = pd.melt(tool_similarity_dataframe.reset_index('doi').rename(columns={'doi': 'source_tool_name'}), id_vars='source_tool_name', var_name='target_tool_name', value_name='similarity').dropna()

	# Remove 0
	melted_tool_similarity_dataframe = melted_tool_similarity_dataframe.loc[[x > 0 for x in melted_tool_similarity_dataframe['similarity']]]
	
	# Get related tools
	related_tool_dataframe = melted_tool_similarity_dataframe.groupby(['source_tool_name'])['target_tool_name','similarity'].apply(lambda x: x.nlargest(5, columns=['similarity'])).reset_index().drop('level_1', axis=1)

	# Get tool keywords
	tool_keyword_dataframe = pd.DataFrame([{'tool_name': tool_dois.get(doi), 'keyword': keyword} for doi, keyword in article_keyword_dataframe.reset_index()[['doi', 'keyword']].as_matrix() ]).dropna()

	# Write
	related_tool_dataframe.to_csv(outfile, sep='\t', index=False)
	tool_keyword_dataframe.to_csv('results/tool_keyword.txt', sep='\t', index=False)

#############################################
########## 5. Get article metrics
#############################################

@transform(prepareArticleTable,
		   suffix('.txt'),
		   '_metrics.txt')

def getArticleMetrics(infile, outfile):

	# Get DOIs
	dois = pd.read_table(infile)['doi'].tolist()[:100]

	# Initialize metrics list
	metrics = []

	# Get scores
	for i, doi in enumerate(dois):
		print i+1
		metrics.append(json.loads(os.popen('python pipeline/get_article_metrics.py '+doi).read()))

	# Convert to dataframe
	metric_score_dataframe = pd.DataFrame(metrics).set_index('doi')

	# Write
	metric_score_dataframe.to_csv(outfile, sep='\t', index=True)

#################################################################
#################################################################
############### 2. Datasets #####################################
#################################################################
#################################################################

#######################################################
#######################################################
########## S1. Annotation and Similarity
#######################################################
#######################################################

#############################################
########## 8. Annotate Datasets
#############################################

@originate('results/dataset.txt')

def annotateDatasets(outfile):

	# Get dataset table
	unannotated_datasets = pd.read_sql_query('SELECT * FROM dataset WHERE dataset_title IS NULL', engine, index_col='id').head()['dataset_accession'].to_dict()

	print unannotated_datasets

	# # Perform dataset query
	# unannotated_datasets_query = session.query(metadata.tables['dataset'].columns['dataset_accession']).filter(and_(or_(metadata.tables['dataset'].columns['dataset_accession'].like('GSE%'), metadata.tables['dataset'].columns['dataset_accession'].like('GDS%')), metadata.tables['dataset'].columns['dataset_title'] == None)).all()

	# # Loop through datasets
	# for unannotated_dataset in unannotated_datasets_query:
	# 	print unannotated_dataset
	# 	# Get annotation
	# 	dataset_annotation = json.loads(os.popen('python pipeline/annotate_dataset.py '+unannotated_dataset[0]).read())
		
	# 	# Update
	# 	session.execute(metadata.tables['dataset'].update().values(dataset_annotation).where(metadata.tables['dataset'].columns['dataset_accession'] == unannotated_dataset[0]))

	# # Commit session
	# session.commit()

#############################################
########## 9. Dataset Similarity
#############################################

@follows(mkdir('09-dataset_similarity'))

@originate('09-dataset_similarity/dataset_similarity.txt')

def getDatasetSimilarity(outfile):

	# Get dataset dataframe
	dataset_dataframe = pd.read_sql_query('SELECT * FROM dataset WHERE dataset_title IS NOT NULL', engine)

	# Get processed text
	processed_texts = [P.process_text(x) for x in dataset_dataframe['dataset_title']+dataset_dataframe['dataset_description']]

	# Get similarity and keywords
	similarity_dataframe, keyword_dataframe = P.extract_text_similarity_and_keywords(processed_texts, labels=dataset_dataframe['dataset_accession'], identifier='dataset_accession')

	# Fill diagonal
	np.fill_diagonal(similarity_dataframe.values, np.nan)

	# Melt tool similarity
	similarity_dataframe = pd.melt(similarity_dataframe.reset_index('dataset_accession').rename(columns={'dataset_accession': 'source_dataset_accession'}), id_vars='source_dataset_accession', var_name='target_dataset_accession', value_name='similarity').dropna()

	# Write
	keyword_dataframe.to_csv(outfile.replace('similarity.txt', 'keywords.txt'), sep='\t')
	similarity_dataframe.to_csv(outfile, sep='\t', index=False)

#############################################
########## 10. Upload Dataset Data
#############################################

@follows(mkdir('10-upload_dataset_data'))

@follows(getDatasetSimilarity)

@files(glob.glob('09-dataset_similarity/*.txt'),
	   '10-upload_dataset_data/upload_dataset_data.txt')

def uploadDatasetData(infiles, outfile):

	# Split infiles
	keywordFile, similarityFile = infiles

	# Read dataset similarity dataframe
	dataset_similarity_dataframe = pd.read_table(similarityFile)

	# Get dataset ID dataframe
	dataset_id_dataframe = pd.read_sql_query('SELECT id AS dataset_fk, dataset_accession FROM dataset', engine)

	# Truncate similarity
	engine.execute('TRUNCATE TABLE related_dataset;')

	# Prepare dataframes ready to upload
	dataframes_ready_to_upload = {
		'related_dataset': dataset_similarity_dataframe.groupby(['source_dataset_accession'])['target_dataset_accession','similarity'].apply(lambda x: x.nlargest(10, columns=['similarity'])).reset_index().drop('level_1', axis=1).merge(dataset_id_dataframe, left_on='source_dataset_accession', right_on='dataset_accession', how='left').rename(columns={'dataset_fk': 'source_dataset_fk'}).merge(dataset_id_dataframe, left_on='target_dataset_accession', right_on='dataset_accession', how='left').rename(columns={'dataset_fk': 'target_dataset_fk'})[['source_dataset_fk', 'target_dataset_fk', 'similarity']].dropna(),
		'keyword': pd.read_table(keywordFile).merge(dataset_id_dataframe, on='dataset_accession', how='left')[['dataset_fk', 'keyword']].dropna()
	}

	# Loop through prepared dataframes
	for table_name, dataframe_ready_to_upload in dataframes_ready_to_upload.iteritems():

		# Upload
		engine.execute('SET GLOBAL max_allowed_packet=1073741824;')
		engine.execute(Table(table_name, MetaData(), autoload=True, autoload_with=engine).insert().prefix_with('IGNORE'), dataframe_ready_to_upload.to_dict(orient='records'))



##################################################
##################################################
########## Run pipeline
##################################################
##################################################
pipeline_run([sys.argv[-1]], multiprocess=2, verbose=1)
print('Done!')
