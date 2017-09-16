# System packages
import scrapy, os               # Basic formatting
import datetime, pytz           # Date, time handling
import re, json                 # string parser

# Project utils
from scrapy.utils.project import get_project_settings       # Get settings dynamically
from oilgas.utils.logger import Logger                      # My logger lol
from oilgas.items import Presentation                       # Items, pippelines


SPIDER_NAME = "oasisinvestors"

logger = Logger(spider=SPIDER_NAME)
settings = get_project_settings()


class SlideSpider(scrapy.Spider):
    # name:
    # Should be unique among your spiders,
    name = SPIDER_NAME
    domain = 'http://oasispetroleum.investorroom.com/'
    directory_name = 'OASIS'
    date_format = ['%B %d%Y', '%b %Y']


    url_load_more_format = 'http://oasispetroleum.investorroom.com/events?ajax=ajax&op=list&direction=past&limit_date={limit_date}&start_date={last_start}'
    url_items_format = 'http://oasispetroleum.investorroom.com/events?item=%s'
    recursive_count = 10  # How many load more you wanna click on
    # Websites to scrape from
    urls = ['http://oasispetroleum.investorroom.com/events?ajax=ajax&op=list&direction=past']

    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(
                url = url,
                callback = self.parse,
                meta = {
                    'recursive_count': self.recursive_count
                }
            )

    def parse(self, response):

        ## add your selector here
        body = scrapy.Selector(response)
        recursive_count = int(response.meta.get('recursive_count', 0))

        logger.debug('Begin Parse.')
        s = ''.join(body.xpath('.//text()').extract())
        s = re.sub(r'(\\n)|(\\r)|(\\b)|(\\t)|(\\u)', '', s)
        js = json.loads(s)


        for d in js['items']:
            if d.get('content', '').find('nvestor Presentation') >= 0:
                item_id = d.get('id')
                m = re.match(r'wd_event_([0-9]+)_', item_id)
                if m:
                    item = m.group(1)
                    next_url = self.url_items_format % item
                    yield scrapy.Request(
                        url = next_url,
                        callback = self.parse_items
                    )


        # Now we check if we need more parse such as next page or load mores...
        if recursive_count > 0:
            js['limit_date'] = datetime.date.today().strftime('%Y-%m-%d')
            next_url = self.url_load_more_format.format(**js)
            logger.debug('Retrieve Next Page - %s' % next_url)
            yield scrapy.Request(
                url = next_url,
                callback = self.parse,
                meta = {
                    'recursive_count' : recursive_count - 1
                }
            )

    def parse_items(self, response):
        # body = scrapy.Selector(response)
        # links = body.xpath('//a/@href').re('^.*\\.pdf$')

        link=response.xpath('//a[contains(@href,"download")]/@href').extract()
        if len(link)== 1:
            link = response.xpath('(//a[contains(@href,"download")])[last()]/@href').extract()[0]
            date = response.xpath('//div[@class="wd_featurebox_title"]/text()').extract()[0]
            date = date.split('-')[-1]
            date = date.strip()
        else:
            link=response.xpath('(//a[contains(@href,"download")])[last()]/@href').extract()[0]
            date = response.xpath('//div[@class="item_date wd_event_sidebar_item wd_event_date"]/text()').extract()[0]
            date = [x.strip() for x in date.split(',')]
            date = date[1]+date[2]
        if not link.startswith('http'):
            link = '%s%s' % (self.domain, link)

        filename = link.split('/')[-1]
        # filename = filename[0:filename.find('.')]
        # filename = '%s [%s].pdf' % (filename, date)
        print link
        item = Presentation(
            company='OASIS',
            spider_name=self.name,
            file_url=link,
            file_name=filename,
            created_date=datetime.datetime.now(
                tz=pytz.timezone(settings.get('DEFAULT_TIMEZONE'))
            ),
            file_dir=self.directory_name,
            date=date
        )
        yield item

    #     yield scrapy.Request(
    #         url = link,
    #         callback = self.file_parse,
    #         meta={'date':date}
    #     )
    #
    # def file_parse(self, response):
    #     date = response.meta['date']
    #     link = response.url
    #     filename = link.split('/')[-1]
    #     filename =filename[0:filename.find('.')]
    #     filename = '%s [%s].pdf' % (filename, date)
    #     # try:
    #     #     m = re.match(r'^(.*)-OAS.*pdf$', filename)
    #     #     m = m.groups()[0]
    #     #     # date = datetime.datetime.strptime(m, '%b%y')
    #     # except Exception as e:
    #     #     pass
    #     # Presentation Generation
    #     item = Presentation(
    #         company = 'OASIS',
    #         spider_name = self.name,
    #         file_url = link,
    #         file_name = filename,
    #         created_date = datetime.datetime.now(
    #             tz = pytz.timezone(settings.get('DEFAULT_TIMEZONE'))
    #         ),
    #         file_dir = self.directory_name,
    #         date = date
    #     )
    #
    #     # self.direct_download(link)  # Depricated, use pipeline instead
    #     yield item















    #
    #
    # def direct_download(self, link):
    #     logger.debug('Downloading: %s' % link)
    #
    #     filename = link.split('/')[-1]
    #     response = requests.get(link, stream=True)
    #
    #     #Check directory existence
    #     dir_path = self.directory_name
    #     if not os.path.exists(dir_path):
    #         os.makedirs(dir_path)  # In python3, we can add exist_ok = True
    #
    #     if response.status_code == 200:
    #         # status code == 200 means we successfully establish the connection
    #         # Now we need to read from response and write the content to file
    #         file_path = os.path.join(dir_path, filename)
    #         with open(file_path, 'wb+') as f:
    #             for chunk in response.iter_content(chunk_size=1024 * 16):
    #                 if chunk:  # filter out keep-alive new chunks
    #                     f.write(chunk)
    #     else:
    #         logger.debug('Unable to establish connection!')
    #
    #     response.close()
