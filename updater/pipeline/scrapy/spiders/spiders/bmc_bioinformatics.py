import scrapy, os, json, re
from inline_requests import inline_requests

# Check URL
check_url = lambda x: not any([x.css('::text').extract_first().lower() == 'supplementary data', x.css('::text').extract_first().lower() == 'supplementary information', '@' in x.css('::text').extract_first(), x.css('::attr("href")').extract_first() == None])

class JournalSpider(scrapy.Spider):

    # Setup
    name = "bmc_bioinformatics"
    start_urls = ['https://bmcbioinformatics.biomedcentral.com/articles']

    # Parse archive
    def parse(self, response):

        # Get minimum volume
        from_volume = 18

        # Get volumes
        volumes = set([int(x) for x in response.css('.search__volume-selector option::attr("value")').extract() if x != ''])

        # Get latest volume
        global latest_volume
        latest_volume = max(volumes)

        # Loop through years
        for volume in volumes:

            # Minimum volume
            if volume >= from_volume:
                
                # Parse year
                yield scrapy.Request('https://bmcbioinformatics.biomedcentral.com/articles?query=&volume='+str(volume)+'&searchType=&tab=keyword', callback=self.parse_volume)

    # Parse volume
    @inline_requests
    def parse_volume(self, response):

        # Define articles
        articles = {'article_data': []}

        # Get volume
        volume = re.search('volume=(.*)\&searchType', response.url).group(1)

        # Get base directory
        outfile = os.getcwd().replace('/pipeline/scrapy', '/articles/bmc-bioinformatics/bmc-bioinformatics_vol_')+volume+'.json'

        # Check if outfile exists
        if not os.path.exists(outfile) or int(volume) == latest_volume:

            # Loop through articles
            for i, article_link in enumerate(response.css('.ResultsList .fulltexttitle::attr(href)').extract()):

                # Stop
                if i == 50:
                    break
                
                # Parse archive
                article = yield scrapy.Request('https://bmcbioinformatics.biomedcentral.com'+article_link)

                # Get data
                articles['article_data'].append({
                    'article_title': article.css('.ArticleTitle::text').extract_first(),
                    'authors': [x.replace(u'\u00a0', ' ') for x in article.css('.u-listReset .AuthorName::text').extract()],
                    'doi': article.css('.ArticleDOI a::text').extract_first(),
                    'abstract': [[div.css('.Heading::text').extract_first().strip(), ''.join(div.css('.Para::text, .Para span::text').extract()).strip()] for div in article.css('.Abstract .AbstractSection')],
                    'date': article.css('.HistoryOnlineDate::text').extract_first().replace(u'\u00a0', ' '),
                    'links': list(set([a.css('::attr("href")').extract_first() for a in article.css('.Abstract .AbstractSection a') if check_url(a)]))
                })

            # Save data
            with open(outfile, 'w') as openfile:
                openfile.write(json.dumps(articles, indent=4))

