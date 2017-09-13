# Import modules
import xml.etree.ElementTree as ET
import sys, urllib2, json

# Doi
doi = sys.argv[-1]

# Altmetric API URL
altmetric_url = 'https://api.altmetric.com/v1/doi/'+doi.replace('https://doi.org/', '')

# Read URL
try:

    # Read results
    altmetric_data = json.loads(urllib2.urlopen(altmetric_url).read())

    # PubMed API URL
    pubmed_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id='+altmetric_data['pmid']

    # Read
    pubmed_data = ET.fromstring(urllib2.urlopen('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id='+altmetric_data['pmid']).read())

    # Get data
    metrics_data = {
        'doi': doi,
        'attention_score': altmetric_data['score'],
        'altmetric_badge': altmetric_data['images'].get('small'),
        'attention_percentile': altmetric_data['context']['similar_age_3m']['pct'],
        'citations': int(pubmed_data.find('DocSum/Item[@Name="PmcRefCount"]').text)
    }

except:

    # Return empty dict
    metrics_data = {'doi': doi, 'attention_score': None, 'altmetric_badge':None, 'attention_percentile': None, 'citations': None}

# Return
print json.dumps(metrics_data)