from scrapers.asuratoon import AsuratoonCrawlerFactory


if __name__ == "__main__":
    asuratoon = AsuratoonCrawlerFactory().create_crawler()
    asuratoon.crawl(original_ids=['weapon-maker'])
    asuratoon.push_to_db(type='all', slug_format=False, publish=True)
