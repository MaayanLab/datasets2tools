# Import modules
import xml.etree.ElementTree as ET
import sys, urllib2, json

# Get dataset accession
dataset_accession = sys.argv[-1]

# Get attributes
attributes = ['title', 'summary']

# Check if GEO
if dataset_accession[:3] in ['GDS', 'GSE']:

    url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term={dataset_accession}%5BAccession%20ID%5D'.format(**locals())
    
    # Get GEO ID
    geoId = ET.fromstring(urllib2.urlopen('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term={dataset_accession}%5BAccession%20ID%5D'.format(**locals())).read()).findall('IdList')[0][0].text

    # Get GEO Annotation
    root = ET.fromstring(urllib2.urlopen('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gds&id={geoId}'.format(**locals())).read())
    
    # Convert to dictionary
    annotated_dataset = {x.attrib['Name'].replace('title', 'dataset_title').replace('summary', 'dataset_description'): x.text.encode('ascii', 'ignore').replace('%', '%%').replace('"', "'") for x in root.find('DocSum') if 'Name' in x.attrib.keys() and x.attrib['Name'] in attributes}
    
    # Get landing URL
    annotated_dataset['dataset_landing_url'] = 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc='+dataset_accession if dataset_accession[:3] == 'GDS' else 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc='+dataset_accession
    
    # Add repository FK
    annotated_dataset['repository_fk'] = 1
    
else:
    
    # Return empty
    annotated_dataset = {'title': '', 'summary': '', 'repository_name': '', 'dataset_landing_url': ''}

# Return data
print json.dumps(annotated_dataset)