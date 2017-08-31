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
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import create_engine
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
engine = create_engine('mysql://root:MyNewPass@localhost/datasets2tools')

# Session maker
Session = sessionmaker(bind=engine)

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
########## 3. Article Table
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

	# Write
	article_dataframe.to_csv(outfile, sep='\t', index=False, encoding='utf-8')

#############################################
########## 4. Article Similarity
#############################################

@follows(getArticles)

@follows(mkdir('04-article_similarity'))

@merge(getArticles,
	   '04-article_similarity/article_similarity.txt')

def getArticleSimilarity(infiles, outfile):

	# Initialize dataframe
	abstract_dataframe = pd.concat([pd.read_table(x)[['abstract', 'doi']] for x in infiles])

	# Fix abstract
	abstract_dataframe['abstract'] = [' '.join([abstract_tuple[1] for abstract_tuple in json.loads(x)['abstract'] if abstract_tuple[0] and abstract_tuple[0].lower() not in [u'contact:', u'availability and implementation', u'supplementary information']]) for x in abstract_dataframe['abstract']]

	# Process abstracts
	processed_abstracts = [P.process_text(x) for x in abstract_dataframe['abstract']]

	# Get similarity and keywords
	similarity_dataframe, keyword_dataframe = P.extract_text_similarity_and_keywords(processed_abstracts, labels=abstract_dataframe['doi'])

	# Write
	keyword_dataframe.to_csv(outfile.replace('similarity.txt', 'keywords.txt'), sep='\t', index=True)
	similarity_dataframe.to_csv(outfile, sep='\t', index=True)

#############################################
########## 5. Get article metrics
#############################################

# @follows(getArticleSimilarity)

@follows(mkdir('05-article_metrics'))

@merge(getArticles,
	   '05-article_metrics/article_metrics.txt')

def getArticleMetrics(infiles, outfile):

	os.system('touch '+outfile)

	# # Get DOIs
	# dois = pd.concat([pd.read_table(x)['doi'] for x in infiles]).tolist()[:5]

	# # Get scores
	# metric_score_dataframe = pd.DataFrame({doi: P.metrics_from_doi(doi) for doi in dois})

	# # Write
	# metric_score_dataframe.to_csv(outfile, sep='\t', index=True)

#############################################
########## 6. Tool Similarity
#############################################

# @follows(getArticleSimilarity)

@follows(mkdir('06-tool_similarity'))

@merge([getTools, getArticleSimilarity],
	   '06-tool_similarity/tool_similarity.txt')

def getToolSimilarity(infiles, outfile):

	# Get similarity infile
	similarityInfile = infiles.pop()

	# Concatenate tool dataframe
	tool_dataframe = pd.concat([pd.read_table(x) for x in infiles]).sort_values('tool_name')

	# Get tool-doi correspondence
	tool_dois = tool_dataframe.set_index('doi')['tool_name'].to_dict()

	# Rename similarity
	tool_similarity_dataframe = pd.read_table(similarityInfile, index_col='doi').loc[tool_dois.keys(), tool_dois.keys()].rename(index=tool_dois, columns=tool_dois)

	# Fill diagonal
	np.fill_diagonal(tool_similarity_dataframe.values, np.nan)

	# Melt tool similarity
	melted_tool_similarity_dataframe = pd.melt(tool_similarity_dataframe.reset_index('doi').rename(columns={'doi': 'source_tool_name'}), id_vars='source_tool_name', var_name='target_tool_name', value_name='similarity').dropna()

	# Write
	melted_tool_similarity_dataframe.to_csv(outfile, sep='\t', index=False)

#############################################
########## 7. Upload Data
#############################################

# @follows(getToolSimilarity)

@follows(mkdir('07-upload_data'))

# @files(
		# [['03-articles/bioinformatics/bioinformatics_vol26_issue10_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue11_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue12_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue13_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue14_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue15_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue16_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue17_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue18_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue19_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue1_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue20_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue21_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue22_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue23_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue24_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue2_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue3_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue4_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue5_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue6_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue7_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue8_articles.txt', '03-articles/bioinformatics/bioinformatics_vol26_issue9_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue10_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue11_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue12_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue14_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue15_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue16_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue18_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue19_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue1_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue20_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue21_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue22_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue23_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue24_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue2_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue3_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue4_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue5_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue6_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue7_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue8_articles.txt', '03-articles/bioinformatics/bioinformatics_vol27_issue9_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue10_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue11_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue12_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue13_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue14_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue15_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue16_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue17_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue18_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue19_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue1_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue20_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue21_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue22_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue23_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue24_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue2_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue3_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue4_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue5_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue6_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue7_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue8_articles.txt', '03-articles/bioinformatics/bioinformatics_vol28_issue9_articles.txt', '03-articles/bioinformatics/bioinformatics_vol32_issue20_articles.txt', '03-articles/bioinformatics/bioinformatics_vol32_issue21_articles.txt', '03-articles/bioinformatics/bioinformatics_vol32_issue22_articles.txt', '03-articles/bioinformatics/bioinformatics_vol32_issue23_articles.txt', '03-articles/bioinformatics/bioinformatics_vol32_issue24_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue10_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue11_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue12_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue13_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue14_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue15_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue16_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue17_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue1_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue2_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue3_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue4_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue5_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue6_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue7_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue8_articles.txt', '03-articles/bioinformatics/bioinformatics_vol33_issue9_articles.txt', '03-articles/bmc-bioinformatics/bmc-bioinformatics_vol_10_articles.txt', '03-articles/bmc-bioinformatics/bmc-bioinformatics_vol_11_articles.txt', '03-articles/bmc-bioinformatics/bmc-bioinformatics_vol_12_articles.txt', '03-articles/bmc-bioinformatics/bmc-bioinformatics_vol_13_articles.txt', '03-articles/bmc-bioinformatics/bmc-bioinformatics_vol_14_articles.txt', '03-articles/bmc-bioinformatics/bmc-bioinformatics_vol_15_articles.txt', '03-articles/bmc-bioinformatics/bmc-bioinformatics_vol_16_articles.txt', '03-articles/bmc-bioinformatics/bmc-bioinformatics_vol_17_articles.txt', '03-articles/bmc-bioinformatics/bmc-bioinformatics_vol_18_articles.txt', '03-articles/database/database_vol0_articles.txt', '03-articles/database/database_vol2010_articles.txt', '03-articles/database/database_vol2011_articles.txt', '03-articles/database/database_vol2012_articles.txt', '03-articles/database/database_vol2013_articles.txt', '03-articles/database/database_vol2014_articles.txt', '03-articles/database/database_vol2015_articles.txt', '03-articles/database/database_vol2016_articles.txt', '03-articles/database/database_vol2017_articles.txt', '03-articles/nar/nar_vol41_issue10_articles.txt', '03-articles/nar/nar_vol41_issue11_articles.txt', '03-articles/nar/nar_vol41_issue12_articles.txt', '03-articles/nar/nar_vol41_issue13_articles.txt', '03-articles/nar/nar_vol41_issue14_articles.txt', '03-articles/nar/nar_vol41_issue15_articles.txt', '03-articles/nar/nar_vol41_issue16_articles.txt', '03-articles/nar/nar_vol41_issue17_articles.txt', '03-articles/nar/nar_vol41_issue18_articles.txt', '03-articles/nar/nar_vol41_issue19_articles.txt', '03-articles/nar/nar_vol41_issue1_articles.txt', '03-articles/nar/nar_vol41_issue20_articles.txt', '03-articles/nar/nar_vol41_issue21_articles.txt', '03-articles/nar/nar_vol41_issue22_articles.txt', '03-articles/nar/nar_vol41_issue2_articles.txt', '03-articles/nar/nar_vol41_issue3_articles.txt', '03-articles/nar/nar_vol41_issue4_articles.txt', '03-articles/nar/nar_vol41_issue5_articles.txt', '03-articles/nar/nar_vol41_issue6_articles.txt', '03-articles/nar/nar_vol41_issue7_articles.txt', '03-articles/nar/nar_vol41_issue8_articles.txt', '03-articles/nar/nar_vol41_issue9_articles.txt', '03-articles/nar/nar_vol41_issueD1_articles.txt', '03-articles/nar/nar_vol41_issueW1_articles.txt', '03-articles/nar/nar_vol42_issue10_articles.txt', '03-articles/nar/nar_vol42_issue11_articles.txt', '03-articles/nar/nar_vol42_issue12_articles.txt', '03-articles/nar/nar_vol42_issue13_articles.txt', '03-articles/nar/nar_vol42_issue14_articles.txt', '03-articles/nar/nar_vol42_issue15_articles.txt', '03-articles/nar/nar_vol42_issue16_articles.txt', '03-articles/nar/nar_vol42_issue17_articles.txt', '03-articles/nar/nar_vol42_issue18_articles.txt', '03-articles/nar/nar_vol42_issue19_articles.txt', '03-articles/nar/nar_vol42_issue1_articles.txt', '03-articles/nar/nar_vol42_issue20_articles.txt', '03-articles/nar/nar_vol42_issue21_articles.txt', '03-articles/nar/nar_vol42_issue22_articles.txt', '03-articles/nar/nar_vol42_issue2_articles.txt', '03-articles/nar/nar_vol42_issue3_articles.txt', '03-articles/nar/nar_vol42_issue4_articles.txt', '03-articles/nar/nar_vol42_issue5_articles.txt', '03-articles/nar/nar_vol42_issue6_articles.txt', '03-articles/nar/nar_vol42_issue7_articles.txt', '03-articles/nar/nar_vol42_issue8_articles.txt', '03-articles/nar/nar_vol42_issue9_articles.txt', '03-articles/nar/nar_vol42_issueD1_articles.txt', '03-articles/nar/nar_vol42_issueW1_articles.txt', '03-articles/nar/nar_vol43_issue10_articles.txt', '03-articles/nar/nar_vol43_issue11_articles.txt', '03-articles/nar/nar_vol43_issue13_articles.txt', '03-articles/nar/nar_vol43_issue15_articles.txt', '03-articles/nar/nar_vol43_issue16_articles.txt', '03-articles/nar/nar_vol43_issue17_articles.txt', '03-articles/nar/nar_vol43_issue18_articles.txt', '03-articles/nar/nar_vol43_issue19_articles.txt', '03-articles/nar/nar_vol43_issue1_articles.txt', '03-articles/nar/nar_vol43_issue20_articles.txt', '03-articles/nar/nar_vol43_issue21_articles.txt', '03-articles/nar/nar_vol43_issue22_articles.txt', '03-articles/nar/nar_vol43_issue3_articles.txt', '03-articles/nar/nar_vol43_issue4_articles.txt', '03-articles/nar/nar_vol43_issue6_articles.txt', '03-articles/nar/nar_vol43_issue8_articles.txt', '03-articles/nar/nar_vol43_issue9_articles.txt', '03-articles/nar/nar_vol44_issue10_articles.txt', '03-articles/nar/nar_vol44_issue11_articles.txt', '03-articles/nar/nar_vol44_issue12_articles.txt', '03-articles/nar/nar_vol44_issue13_articles.txt', '03-articles/nar/nar_vol44_issue14_articles.txt', '03-articles/nar/nar_vol44_issue15_articles.txt', '03-articles/nar/nar_vol44_issue16_articles.txt', '03-articles/nar/nar_vol44_issue17_articles.txt', '03-articles/nar/nar_vol44_issue18_articles.txt', '03-articles/nar/nar_vol44_issue19_articles.txt', '03-articles/nar/nar_vol44_issue1_articles.txt', '03-articles/nar/nar_vol44_issue20_articles.txt', '03-articles/nar/nar_vol44_issue21_articles.txt', '03-articles/nar/nar_vol44_issue22_articles.txt', '03-articles/nar/nar_vol44_issue2_articles.txt', '03-articles/nar/nar_vol44_issue3_articles.txt', '03-articles/nar/nar_vol44_issue4_articles.txt', '03-articles/nar/nar_vol44_issue5_articles.txt', '03-articles/nar/nar_vol44_issue6_articles.txt', '03-articles/nar/nar_vol44_issue7_articles.txt', '03-articles/nar/nar_vol44_issue8_articles.txt', '03-articles/nar/nar_vol44_issue9_articles.txt', '03-articles/nar/nar_vol44_issueD1_articles.txt', '03-articles/nar/nar_vol44_issueW1_articles.txt', '03-articles/nar/nar_vol45_issue10_articles.txt', '03-articles/nar/nar_vol45_issue11_articles.txt', '03-articles/nar/nar_vol45_issue12_articles.txt', '03-articles/nar/nar_vol45_issue13_articles.txt', '03-articles/nar/nar_vol45_issue14_articles.txt', '03-articles/nar/nar_vol45_issue1_articles.txt', '03-articles/nar/nar_vol45_issue2_articles.txt', '03-articles/nar/nar_vol45_issue3_articles.txt', '03-articles/nar/nar_vol45_issue4_articles.txt', '03-articles/nar/nar_vol45_issue5_articles.txt', '03-articles/nar/nar_vol45_issue6_articles.txt', '03-articles/nar/nar_vol45_issue7_articles.txt', '03-articles/nar/nar_vol45_issue8_articles.txt', '03-articles/nar/nar_vol45_issue9_articles.txt', '03-articles/nar/nar_vol45_issueD1_articles.txt', '03-articles/nar/nar_vol45_issueW1_articles.txt'], ['02-tools/bioinformatics/bioinformatics_vol26_issue10_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue11_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue12_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue13_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue14_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue15_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue16_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue17_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue18_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue19_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue1_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue20_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue21_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue22_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue23_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue24_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue2_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue3_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue4_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue5_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue6_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue7_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue8_tools.txt', '02-tools/bioinformatics/bioinformatics_vol26_issue9_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue10_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue11_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue12_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue14_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue15_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue16_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue18_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue19_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue1_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue20_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue21_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue22_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue23_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue24_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue2_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue3_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue4_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue5_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue6_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue7_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue8_tools.txt', '02-tools/bioinformatics/bioinformatics_vol27_issue9_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue10_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue11_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue12_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue13_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue14_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue15_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue16_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue17_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue18_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue19_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue1_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue20_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue21_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue22_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue23_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue24_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue2_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue3_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue4_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue5_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue6_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue7_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue8_tools.txt', '02-tools/bioinformatics/bioinformatics_vol28_issue9_tools.txt', '02-tools/bioinformatics/bioinformatics_vol32_issue20_tools.txt', '02-tools/bioinformatics/bioinformatics_vol32_issue21_tools.txt', '02-tools/bioinformatics/bioinformatics_vol32_issue22_tools.txt', '02-tools/bioinformatics/bioinformatics_vol32_issue23_tools.txt', '02-tools/bioinformatics/bioinformatics_vol32_issue24_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue10_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue11_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue12_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue13_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue14_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue15_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue16_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue17_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue1_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue2_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue3_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue4_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue5_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue6_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue7_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue8_tools.txt', '02-tools/bioinformatics/bioinformatics_vol33_issue9_tools.txt', '02-tools/bmc-bioinformatics/bmc-bioinformatics_vol_10_tools.txt', '02-tools/bmc-bioinformatics/bmc-bioinformatics_vol_11_tools.txt', '02-tools/bmc-bioinformatics/bmc-bioinformatics_vol_12_tools.txt', '02-tools/bmc-bioinformatics/bmc-bioinformatics_vol_13_tools.txt', '02-tools/bmc-bioinformatics/bmc-bioinformatics_vol_14_tools.txt', '02-tools/bmc-bioinformatics/bmc-bioinformatics_vol_15_tools.txt', '02-tools/bmc-bioinformatics/bmc-bioinformatics_vol_16_tools.txt', '02-tools/bmc-bioinformatics/bmc-bioinformatics_vol_17_tools.txt', '02-tools/bmc-bioinformatics/bmc-bioinformatics_vol_18_tools.txt', '02-tools/database/database_vol0_tools.txt', '02-tools/database/database_vol2010_tools.txt', '02-tools/database/database_vol2011_tools.txt', '02-tools/database/database_vol2012_tools.txt', '02-tools/database/database_vol2013_tools.txt', '02-tools/database/database_vol2014_tools.txt', '02-tools/database/database_vol2015_tools.txt', '02-tools/database/database_vol2016_tools.txt', '02-tools/database/database_vol2017_tools.txt', '02-tools/nar/nar_vol41_issue10_tools.txt', '02-tools/nar/nar_vol41_issue11_tools.txt', '02-tools/nar/nar_vol41_issue12_tools.txt', '02-tools/nar/nar_vol41_issue13_tools.txt', '02-tools/nar/nar_vol41_issue14_tools.txt', '02-tools/nar/nar_vol41_issue15_tools.txt', '02-tools/nar/nar_vol41_issue16_tools.txt', '02-tools/nar/nar_vol41_issue17_tools.txt', '02-tools/nar/nar_vol41_issue18_tools.txt', '02-tools/nar/nar_vol41_issue19_tools.txt', '02-tools/nar/nar_vol41_issue1_tools.txt', '02-tools/nar/nar_vol41_issue20_tools.txt', '02-tools/nar/nar_vol41_issue21_tools.txt', '02-tools/nar/nar_vol41_issue22_tools.txt', '02-tools/nar/nar_vol41_issue2_tools.txt', '02-tools/nar/nar_vol41_issue3_tools.txt', '02-tools/nar/nar_vol41_issue4_tools.txt', '02-tools/nar/nar_vol41_issue5_tools.txt', '02-tools/nar/nar_vol41_issue6_tools.txt', '02-tools/nar/nar_vol41_issue7_tools.txt', '02-tools/nar/nar_vol41_issue8_tools.txt', '02-tools/nar/nar_vol41_issue9_tools.txt', '02-tools/nar/nar_vol41_issueD1_tools.txt', '02-tools/nar/nar_vol41_issueW1_tools.txt', '02-tools/nar/nar_vol42_issue10_tools.txt', '02-tools/nar/nar_vol42_issue11_tools.txt', '02-tools/nar/nar_vol42_issue12_tools.txt', '02-tools/nar/nar_vol42_issue13_tools.txt', '02-tools/nar/nar_vol42_issue14_tools.txt', '02-tools/nar/nar_vol42_issue15_tools.txt', '02-tools/nar/nar_vol42_issue16_tools.txt', '02-tools/nar/nar_vol42_issue17_tools.txt', '02-tools/nar/nar_vol42_issue18_tools.txt', '02-tools/nar/nar_vol42_issue19_tools.txt', '02-tools/nar/nar_vol42_issue1_tools.txt', '02-tools/nar/nar_vol42_issue20_tools.txt', '02-tools/nar/nar_vol42_issue21_tools.txt', '02-tools/nar/nar_vol42_issue22_tools.txt', '02-tools/nar/nar_vol42_issue2_tools.txt', '02-tools/nar/nar_vol42_issue3_tools.txt', '02-tools/nar/nar_vol42_issue4_tools.txt', '02-tools/nar/nar_vol42_issue5_tools.txt', '02-tools/nar/nar_vol42_issue6_tools.txt', '02-tools/nar/nar_vol42_issue7_tools.txt', '02-tools/nar/nar_vol42_issue8_tools.txt', '02-tools/nar/nar_vol42_issue9_tools.txt', '02-tools/nar/nar_vol42_issueD1_tools.txt', '02-tools/nar/nar_vol42_issueW1_tools.txt', '02-tools/nar/nar_vol43_issue10_tools.txt', '02-tools/nar/nar_vol43_issue11_tools.txt', '02-tools/nar/nar_vol43_issue13_tools.txt', '02-tools/nar/nar_vol43_issue15_tools.txt', '02-tools/nar/nar_vol43_issue16_tools.txt', '02-tools/nar/nar_vol43_issue17_tools.txt', '02-tools/nar/nar_vol43_issue18_tools.txt', '02-tools/nar/nar_vol43_issue19_tools.txt', '02-tools/nar/nar_vol43_issue1_tools.txt', '02-tools/nar/nar_vol43_issue20_tools.txt', '02-tools/nar/nar_vol43_issue21_tools.txt', '02-tools/nar/nar_vol43_issue22_tools.txt', '02-tools/nar/nar_vol43_issue3_tools.txt', '02-tools/nar/nar_vol43_issue4_tools.txt', '02-tools/nar/nar_vol43_issue6_tools.txt', '02-tools/nar/nar_vol43_issue8_tools.txt', '02-tools/nar/nar_vol43_issue9_tools.txt', '02-tools/nar/nar_vol44_issue10_tools.txt', '02-tools/nar/nar_vol44_issue11_tools.txt', '02-tools/nar/nar_vol44_issue12_tools.txt', '02-tools/nar/nar_vol44_issue13_tools.txt', '02-tools/nar/nar_vol44_issue14_tools.txt', '02-tools/nar/nar_vol44_issue15_tools.txt', '02-tools/nar/nar_vol44_issue16_tools.txt', '02-tools/nar/nar_vol44_issue17_tools.txt', '02-tools/nar/nar_vol44_issue18_tools.txt', '02-tools/nar/nar_vol44_issue19_tools.txt', '02-tools/nar/nar_vol44_issue1_tools.txt', '02-tools/nar/nar_vol44_issue20_tools.txt', '02-tools/nar/nar_vol44_issue21_tools.txt', '02-tools/nar/nar_vol44_issue22_tools.txt', '02-tools/nar/nar_vol44_issue2_tools.txt', '02-tools/nar/nar_vol44_issue3_tools.txt', '02-tools/nar/nar_vol44_issue4_tools.txt', '02-tools/nar/nar_vol44_issue5_tools.txt', '02-tools/nar/nar_vol44_issue6_tools.txt', '02-tools/nar/nar_vol44_issue7_tools.txt', '02-tools/nar/nar_vol44_issue8_tools.txt', '02-tools/nar/nar_vol44_issue9_tools.txt', '02-tools/nar/nar_vol44_issueD1_tools.txt', '02-tools/nar/nar_vol44_issueW1_tools.txt', '02-tools/nar/nar_vol45_issue10_tools.txt', '02-tools/nar/nar_vol45_issue11_tools.txt', '02-tools/nar/nar_vol45_issue12_tools.txt', '02-tools/nar/nar_vol45_issue13_tools.txt', '02-tools/nar/nar_vol45_issue14_tools.txt', '02-tools/nar/nar_vol45_issue1_tools.txt', '02-tools/nar/nar_vol45_issue2_tools.txt', '02-tools/nar/nar_vol45_issue3_tools.txt', '02-tools/nar/nar_vol45_issue4_tools.txt', '02-tools/nar/nar_vol45_issue5_tools.txt', '02-tools/nar/nar_vol45_issue6_tools.txt', '02-tools/nar/nar_vol45_issue7_tools.txt', '02-tools/nar/nar_vol45_issue8_tools.txt', '02-tools/nar/nar_vol45_issue9_tools.txt', '02-tools/nar/nar_vol45_issueD1_tools.txt', '02-tools/nar/nar_vol45_issueW1_tools.txt'], '04-article_similarity/article_keywords.txt', '05-article_metrics/article_metrics.txt', '06-tool_similarity/tool_similarity.txt'],
@files([[getArticles], [getTools], '04-article_similarity/article_keywords.txt', getArticleMetrics, getToolSimilarity],
	   '07-upload_data/upload_data.txt')

def uploadData(infiles, outfile):

	# Split infiles
	articleFiles, toolFiles, keywordFile, metricsFile, similarityFile = infiles

	# Get article dataframe
	article_dataframe =  P.fix_dates(pd.concat([pd.read_table(x) for x in articleFiles]))

	# Get tool dataframe
	tool_dataframe =  pd.concat([pd.read_table(x) for x in toolFiles])

	# Create session
	session = Session()

	# Upload and get IDs of tools 
	tool_id_dataframe = P.upload_and_get_ids(tool_dataframe, table_name='tool', engine=engine)

	# Commit
	session.commit()

	# Prepare dataframes ready to upload
	dataframes_ready_to_upload = {
		'article': article_dataframe.merge(tool_dataframe[['doi', 'tool_name']], on='doi', how='left').merge(tool_id_dataframe, on='tool_name', how='left').drop('tool_name', axis=1).dropna(),
		'related_tool': pd.read_table(similarityFile).groupby(['source_tool_name'])['target_tool_name','similarity'].apply(lambda x: x.nlargest(10, columns=['similarity'])).reset_index().drop('level_1', axis=1).merge(tool_id_dataframe, left_on='source_tool_name', right_on='tool_name', how='left').rename(columns={'tool_fk': 'source_tool_fk'}).merge(tool_id_dataframe, left_on='target_tool_name', right_on='tool_name', how='left').rename(columns={'tool_fk': 'target_tool_fk'})[['source_tool_fk', 'target_tool_fk', 'similarity']].dropna()
	}

	# Truncate similarity
	engine.execute('TRUNCATE TABLE related_tool;')

	# Loop through prepared dataframes
	for table_name, dataframe_ready_to_upload in dataframes_ready_to_upload.iteritems():

		# Upload
		engine.execute(Table(table_name, MetaData(), autoload=True, autoload_with=engine).insert().prefix_with('IGNORE'), dataframe_ready_to_upload.to_dict(orient='records'))



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
