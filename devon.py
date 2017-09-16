# System packages
import scrapy, os  # Basic formatting
import datetime, pytz  # Date, time handling
import re, json  # string parser

# Project utils
from scrapy.utils.project import get_project_settings  # Get settings dynamically
from oilgas.utils.logger import Logger  # My logger lol
from oilgas.items import Presentation  # Items, pippelines

SPIDER_NAME = "dvninvestors"

logger = Logger(spider=SPIDER_NAME)
settings = get_project_settings()


class SlideSpider(scrapy.Spider):
    # name:
    # Should be unique among your spiders,
    name = SPIDER_NAME
    domain = 'http://'
    directory_name = 'DEVON'
    date_format=['%m/%d/%Y %H:%M:%S']

    # Websites to scrape from
    urls = [
        'http://investors.devonenergy.com/investors/events-presentations/default.aspx'
    ]

    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        body=scrapy.Selector(response)
        content=body.extract()
        ##get signature
        ind = content.find('function GetSignature(){')
        m = re.match(r'^.*\{ return \'([a-zA-Z0-9]+)', content[ind:(ind + 80)])
        signature = m.groups()[0]

        now = datetime.datetime.now()

        data = {
            "serviceData": {
                "serviceDto": {
                    "ViewType": "2",
                    "ViewDate": datetime.datetime.strftime(now, '%Y-%m-%dT%H-%M-%S'),
                    "RevisionNumber": "1",
                    "LanguageId": "1",
                    "ItemCount": -1,
                    "IncludeTags": True,
                    "StartIndex": 0,
                    "Signature": signature
                },
                "eventSelection": 0,
                "year": -1,
                "sortOperator": 1,
                "includePressReleases": True,
                "includePresentations": True,
                "includeFinancialReports": True
            }
        }
        headers_get = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
            'Accept': 'application/json, charset=utf-8, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
        }
        url_next = 'http://investors.devonenergy.com/services/EventService.svc/GetEventList'
        headers_post = headers_get
        headers_post['Content-Type'] = 'application/json; charset=utf-8'
        yield scrapy.Request(url_next, method='POST',
                          body=json.dumps(data["serviceData"]),
                              headers=headers_post,
                                 callback=self.parse_item)


    def parse_item(self, response):
        info = json.loads(response.body_as_unicode())
        for doc in info['GetEventListResult']:
            try:
                date=doc['StartDate']
                filename=doc['Title']
                if doc['DocumentPath'] is None: ## filter for presentation
                    for presentation in doc['EventPresentation']:
                        link=presentation['DocumentPath']
                else: ##
                    link=doc['DocumentPath']
                item = Presentation(
                    company='DEVON',
                    spider_name=self.name,
                    file_dir=self.directory_name,
                    date=date,
                    file_url=link,
                    created_date=datetime.datetime.now(tz=pytz.timezone(settings.get('DEFAULT_TIMEZONE'))),
                    file_name=filename
                )
                yield item
            except:
                continue