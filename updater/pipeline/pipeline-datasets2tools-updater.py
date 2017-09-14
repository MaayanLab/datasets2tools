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
########## 1. Annotate Datasets
#############################################

@originate('results/dataset.txt')

def annotateDatasets(outfile):

	# Get dataset dataframe
	all_dataset_dataframe = pd.read_sql_query('SELECT * FROM dataset', engine).set_index('dataset_accession', drop=False)

	# Get dataset table
	unannotated_dataset_accessions = [dataset_accession for dataset_accession, dataset_title in all_dataset_dataframe[['dataset_accession', 'dataset_title']].as_matrix() if not dataset_title]

	# Initialize annotation dict
	annotation_dict = {}

	# Get annotations
	for i, dataset_accession in enumerate(unannotated_dataset_accessions):
		print i+1
		try:
			annotation_dict[dataset_accession] = json.loads(os.popen('python pipeline/annotate_dataset.py ' + dataset_accession).read())
		except:
			pass

	# Update
	all_dataset_dataframe.update(pd.DataFrame(annotation_dict).T)

	# Write
	all_dataset_dataframe.to_csv(outfile, sep='\t', index=False)

#############################################
########## 2. Dataset Similarity
#############################################

@transform(annotateDatasets,
		   regex(r'(.*)/(.*).txt'),
		   r'\1/related_\2.txt')

def getRelatedDatasets(infile, outfile):

	# Get dataset dataframe
	dataset_dataframe = pd.read_table(infile)

	# Get processed text
	processed_texts = [P.process_text(x) for x in dataset_dataframe['dataset_title']+dataset_dataframe['dataset_description']]

	# Get similarity and keywords
	dataset_similarity_dataframe, dataset_keyword_dataframe = P.extract_text_similarity_and_keywords(processed_texts, labels=dataset_dataframe['dataset_accession'], identifier='dataset_accession')

	# Fill diagonal
	np.fill_diagonal(dataset_similarity_dataframe.values, np.nan)

	# Melt dataset similarity
	melted_dataset_similarity_dataframe = pd.melt(dataset_similarity_dataframe.reset_index('dataset_accession').rename(columns={'dataset_accession': 'source_dataset_accession'}), id_vars='source_dataset_accession', var_name='target_dataset_accession', value_name='similarity').dropna()

	# Remove 0
	melted_dataset_similarity_dataframe = melted_dataset_similarity_dataframe.loc[[x > 0 for x in melted_dataset_similarity_dataframe['similarity']]]
	
	# Get related datasets
	related_dataset_dataframe = melted_dataset_similarity_dataframe.groupby(['source_dataset_accession'])['target_dataset_accession','similarity'].apply(lambda x: x.nlargest(5, columns=['similarity'])).reset_index().drop('level_1', axis=1)

	# Write
	related_dataset_dataframe.to_csv(outfile, sep='\t', index=False)
	dataset_keyword_dataframe.to_csv('results/dataset_keyword.txt', sep='\t', index=True)

#################################################################
#################################################################
############### 3. Canned Analyses ##############################
#################################################################
#################################################################

#######################################################
#######################################################
########## S1. Similarity
#######################################################
#######################################################

#############################################
########## 1. Canned Analysis Similarity
#############################################

@originate('results/related_canned_analysis.txt')

def getRelatedAnalyses(outfile):

	# Get canned analysis dataframe
	canned_analysis_dataframe = pd.read_sql_query('SELECT canned_analysis_accession, canned_analysis_title, canned_analysis_description FROM canned_analysis', engine)

	# Get processed text
	processed_texts = [P.process_text(x) for x in canned_analysis_dataframe['canned_analysis_title']+canned_analysis_dataframe['canned_analysis_description']]

	# Get similarity and keywords
	canned_analysis_similarity_dataframe, canned_analysis_keyword_dataframe = P.extract_text_similarity_and_keywords(processed_texts, labels=canned_analysis_dataframe['canned_analysis_accession'], identifier='canned_analysis_accession')

	# Fill diagonal
	np.fill_diagonal(canned_analysis_similarity_dataframe.values, np.nan)

	# Melt analysis similarity
	melted_canned_analysis_similarity_dataframe = pd.melt(canned_analysis_similarity_dataframe.reset_index('canned_analysis_accession').rename(columns={'canned_analysis_accession': 'source_canned_analysis_accession'}), id_vars='source_canned_analysis_accession', var_name='target_canned_analysis_accession', value_name='similarity').dropna()

	# Remove 0
	melted_canned_analysis_similarity_dataframe = melted_canned_analysis_similarity_dataframe.loc[[x > 0 for x in melted_canned_analysis_similarity_dataframe['similarity']]]
	
	# Get related analyses
	related_canned_analysis_dataframe = melted_canned_analysis_similarity_dataframe.groupby(['source_canned_analysis_accession'])['target_canned_analysis_accession','similarity'].apply(lambda x: x.nlargest(5, columns=['similarity'])).reset_index().drop('level_1', axis=1)

	# Write
	related_canned_analysis_dataframe.to_csv(outfile, sep='\t', index=False)

##################################################
##################################################
########## Run pipeline
##################################################
##################################################
pipeline_run([sys.argv[-1]], multiprocess=2, verbose=1)
print('Done!')
