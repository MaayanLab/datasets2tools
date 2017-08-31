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
import sys, os, glob, json, urllib2
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

##### 2. Custom modules #####
# Pipeline running
sys.path.append('pipeline')
import PipelineDatasets2ToolsUpdater as P

#############################################
########## 2. General Setup
#############################################
##### 1. Variables #####
spiders = ['oxford', 'bmc_bioinformatics']

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
########## 2. Tool Table
#############################################

@follows(runSpiders)

@follows(mkdir('02-tools'))

@collate(glob.glob('01-journals/*/*.json'),
		 regex(r'01-journals/(.*)/.*.json'),
		 r'02-tools/\1_tools.txt')

def getTools(infiles, outfile):

	# Initialize dataframe
	tool_dataframe = pd.DataFrame()

	# Loop through infiles
	for infile in infiles:

		# Get dataframe
		with open(infile, 'r') as openfile:

			# Get dataframe
			dataframe_to_append = pd.DataFrame(json.loads(openfile.read())['article_data'])[['article_title', 'links', 'doi']]
			
			# Drop no links
			dataframe_to_append.drop([index for index, rowData in dataframe_to_append.iterrows() if len(rowData['links']) == 0], inplace=True)
			
			# Add link column
			dataframe_to_append['link'] = [x[0] for x in dataframe_to_append['links']]

			# Drop links columns
			dataframe_to_append.drop('links', inplace=True, axis=1)
			
			# Add tool name column
			dataframe_to_append['tool_name'] = [x.split(':')[0] if ':' in x else None for x in dataframe_to_append['article_title']]
			
			# Drop rows with no names
			dataframe_to_append.drop([index for index, rowData in dataframe_to_append.iterrows() if not rowData['tool_name']], inplace=True)

			# Add tool description
			dataframe_to_append['tool_description'] = [x.split(':', 1)[-1].strip() for x in dataframe_to_append['article_title']]
			dataframe_to_append['tool_description'] = [x[0].upper()+x[1:] for x in dataframe_to_append['tool_description']]
			
			# Drop article title
			dataframe_to_append.drop('article_title', inplace=True, axis=1)
			
			# Concatenate
			tool_dataframe = pd.concat([tool_dataframe, dataframe_to_append]).reset_index(drop=True)

	# # Check if tool link works
	# indices_to_drop = []

	# # Loop through indicies
	# for index, rowData in tool_dataframe.iterrows():

	# 	# Try to connect
	# 	try:

	# 		if urllib2.urlopen(rowData['link']).getcode() in (200, 401):
	# 			pass
	# 		else:
	# 			# Append
	# 			indices_to_drop.append(index)
	# 	except:
	# 		# Append
	# 		indices_to_drop.append(index)

	# # Drop
	# tool_dataframe.drop(indices_to_drop, inplace=True)

	# Write
	tool_dataframe.to_csv(outfile, sep='\t', index=False, encoding='utf-8')

#############################################
########## 3. Article Table
#############################################

# @follows(getTools)

@follows(mkdir('03-articles'))

@collate(glob.glob('01-journals/*/*.json'),
		 regex(r'01-journals/(.*)/.*.json'),
		 add_inputs(r'02-tools/\1_tools.txt'),
		 r'03-articles/\1_articles.txt')

def getArticles(infiles, outfile):

	# Split infiles
	jsonFiles = [x[0] for x in infiles]
	toolFile = infiles[0][1]

	# Initialize dataframe
	article_dataframe = pd.DataFrame()

	# Loop through infiles
	for jsonfile in jsonFiles:

		# Get dataframe
		with open(jsonfile, 'r') as openfile:

			# Get dataframe
			dataframe_to_append = pd.DataFrame(json.loads(openfile.read())['article_data']).drop('links', axis=1)
			
			# Join authors
			dataframe_to_append['authors'] = ['; '.join(x) for x in dataframe_to_append['authors']]
			
			# Fix abstract
			dataframe_to_append['abstract'] = [json.dumps({'abstract': x}) for x in dataframe_to_append['abstract']]
			
			# Concatenate
			article_dataframe = pd.concat([article_dataframe, dataframe_to_append])

	# Get tool DOIs
	toolDois = pd.read_table(toolFile)['doi'].tolist()

	# Intersect
	article_dataframe = article_dataframe.set_index('doi').loc[toolDois].reset_index()

	# Write
	article_dataframe.to_csv(outfile, sep='\t', index=False, encoding='utf-8')

#############################################
########## 4. Article Similarity
#############################################

# @follows(getArticles)

@follows(mkdir('04-article_similarity'))

@merge(getArticles,
	   '04-article_similarity/article_similarity.txt')

def getArticleSimilarity(infiles, outfile):

	# Initialize dataframe
	abstract_dataframe = pd.concat([pd.read_table(x)[['abstract', 'doi']] for x in infiles])

	# Fix abstract
	abstract_dataframe['abstract'] = [' '.join([abstract_tuple[1] for abstract_tuple in json.loads(x)['abstract'] if abstract_tuple[0] not in [u'Contact:', u'Availability and implementation', u'Supplementary information']]) for x in abstract_dataframe['abstract']]

	# Process abstracts
	processed_abstracts = [P.process_text(x) for x in abstract_dataframe['abstract']]

	# Get similarity and keywords
	similarity_dataframe, keyword_dataframe = P.extract_text_similarity_and_keywords(processed_abstracts, labels=abstract_dataframe['doi'])

	# Write
	similarity_dataframe.to_csv(outfile, sep='\t', index=True)
	keyword_dataframe.to_csv(outfile.replace('similarity.txt', 'keywords.txt'), sep='\t', index=True)

#############################################
########## 5. Tool Similarity
#############################################

# @follows(getArticleSimilarity)

@follows(mkdir('05-tool_similarity'))

@merge((getTools, getArticleSimilarity, '04-article_similarity/article_keywords.txt'),
	   '05-tool_similarity/tool_similarity.txt')

def getToolSimilarity(infiles, outfile):

	# Initialize dataframe
	abstract_dataframe = pd.concat([pd.read_table(x)[['abstract', 'doi']] for x in infiles])

	# Fix abstract
	abstract_dataframe['abstract'] = [' '.join([abstract_tuple[1] for abstract_tuple in json.loads(x)['abstract'] if abstract_tuple[0] not in [u'Contact:', u'Availability and implementation', u'Supplementary information']]) for x in abstract_dataframe['abstract']]

	# Process abstracts
	processed_abstracts = [P.process_text(x) for x in abstract_dataframe['abstract']]

	# Get similarity and keywords
	similarity_dataframe, keyword_dataframe = P.extract_text_similarity_and_keywords(processed_abstracts, labels=abstract_dataframe['doi'])

	# Write
	similarity_dataframe.to_csv(outfile, sep='\t', index=True)
	keyword_dataframe.to_csv(outfile.replace('similarity.txt', 'keywords.txt'), sep='\t', index=True)

#################################################################
#################################################################
############### .  ########################################
#################################################################
#################################################################

#######################################################
#######################################################
########## S1. 
#######################################################
#######################################################

#############################################
########## 1. 
#############################################


##################################################
##################################################
########## Run pipeline
##################################################
##################################################
pipeline_run([sys.argv[-1]], multiprocess=2, verbose=1)
print('Done!')
