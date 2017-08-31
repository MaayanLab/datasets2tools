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
import nltk, re, sklearn
from sklearn.feature_extraction.text import TfidfVectorizer

##### 2. Custom modules #####

#############################################
########## 2. General Setup
#############################################
##### 1. Variables #####
# Define stopwords
stopwords=nltk.corpus.stopwords.words("english")
stopwords.extend(['www','mail','edu','athttps'])

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
#     processed_text = [(word.lower(), penn_to_wn_tags(pos_tag)) for word, pos_tag in tag(" ".join(processed_text))]        
    
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
