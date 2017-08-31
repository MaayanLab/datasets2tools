#################################################################
#################################################################
############### Canned Analyses Support ################
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
import pandas as pd
import nltk, re, sklearn, json, urllib2
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import Table, MetaData
from datetime import datetime

##### 2. Custom modules #####

#############################################
########## 2. General Setup
#############################################
##### 1. Variables #####
# Define stopwords
stopwords=nltk.corpus.stopwords.words("english")
stopwords.extend(['www','mail','edu','athttps', 'doi'])

##### 2. R Connection #####

#################################################################
#################################################################
############### 1. Natural Language Processing ##################
#################################################################
#################################################################

#######################################################
#######################################################
########## S1. Text Similarity 
#######################################################
#######################################################

#############################################
########## 1. Process Text
#############################################

# Process text
def process_text(text):
    
    # Compile regular expression
    remove_characters = re.compile('[^a-zA-Z ]+')
    
    # Remove special characters and make lowercase
    processed_text=re.sub(remove_characters, r'', text.encode('ascii', 'ignore').strip().lower())
    
    # Tokenize
    processed_text = [x.strip() for x in nltk.word_tokenize(processed_text)]

    # Remove stopwords
    processed_text = [x for x in processed_text if x not in stopwords]
    
    # Stem
    # processed_text = [nltk.PorterStemmer().stem(x) for x in processed_text]

    # Tag and make lowercase
#    processed_text = [(word.lower(), penn_to_wn_tags(pos_tag)) for word, pos_tag in tag(" ".join(processed_text))]        
    
    # Check if exists
    processed_text = [x for x in processed_text if nltk.corpus.wordnet.synsets(x)]
    
    # Join
    processed_text = " ".join(processed_text)
    
    # Return
    return processed_text

#############################################
########## 2. Similarity and keywords
#############################################

# Get similarity and keywords
def extract_text_similarity_and_keywords(processed_texts, labels, n_keywords=5):

    # Get vectorized
    tfidf_vectorizer = TfidfVectorizer(min_df=0.00,max_df=1.0, ngram_range=(1, 1))

    # Get matrix
    tfidf_matrix = tfidf_vectorizer.fit_transform(processed_texts).astype(float)

    #Calculate the adjacency matrix
    similarity_dataframe = pd.DataFrame(sklearn.metrics.pairwise.cosine_similarity(tfidf_matrix, tfidf_matrix), index=labels, columns=labels)

    # Feature dataframe
    feature_dataframe = pd.DataFrame(tfidf_matrix.todense(), index=labels, columns=tfidf_vectorizer.get_feature_names())

    # Melt
    feature_dataframe_melted = pd.melt(feature_dataframe.reset_index().rename(columns={'level_0': 'doi'}), id_vars='doi', var_name='word', value_name='importance')

    # Get top keywords dataframe
    keyword_dataframe = feature_dataframe_melted.groupby('doi')['word','importance'].apply(lambda x: x.nlargest(n_keywords, columns=['importance'])).reset_index().set_index('doi').drop_duplicates().drop(['level_1', 'importance'], axis=1)

    # Return
    return similarity_dataframe, keyword_dataframe

#######################################################
#######################################################
########## S2. Article Metrics
#######################################################
#######################################################

#############################################
########## 1. Metrics API
#############################################

def metrics_from_doi(doi):

    # Altmetric API URL
    altmetric_url = 'https://api.altmetric.com/v1/doi/'+doi.replace('https://doi.org/', '')

    # Read URL
    try:

        # Open page
        altmetric_results = urllib2.urlopen(altmetric_url)
        print altmetric_results

        # Read results
        altmetric_data = json.loads(altmetric_results)

        # PubMed API URL
        pubmed_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id='+altmetric_data['pmid']

        # Read
        pubmed_data = ET.fromstring(urllib2.urlopen('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id='+altmetric_data['pmid']).read())

        # Get data
        metrics_data = {
            'attention_score': altmetric_data['score'],
            'attention_percentile': altmetric_data['context']['similar_age_3m']['pct'],
            'citations': int(pubmed_data.find('DocSum/Item[@Name="PmcRefCount"]').text)
        }

    except:

        # Return empty dict
        metrics_data = {'attention_score': None, 'attention_percentile': None, 'citations': None}

    # Return
    return metrics_data

#######################################################
#######################################################
########## S3. Uploading
#######################################################
#######################################################

#############################################
########## 1. Fix dates
#############################################

def fix_dates(dataframe_to_upload, format='%d %B %Y'):

    # Fix date
    dataframe_to_upload['date'] = [datetime.strptime(x, format) for x in dataframe_to_upload['date']]

    # Return
    return dataframe_to_upload


#############################################
########## 2. Get Upload IDs
#############################################

def upload_and_get_ids(dataframe_to_upload, table_name, engine, identifiers={'tool': 'tool_name', 'dataset': 'dataset_accession', 'canned_analysis': 'canned_analysis_url', 'article': 'doi', 'term': 'term_name'}, fix_date='%d %B %Y'):

    # Fix date
    if 'date' in dataframe_to_upload.columns and fix_date:
        dataframe_to_upload = fix_dates(dataframe_to_upload, fix_date)

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