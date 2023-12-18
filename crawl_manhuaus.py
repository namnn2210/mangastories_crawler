from scrapers.manhuaus import ManhuausCrawlerFactory

if __name__ == "__main__":
    manhuaus_crawler = ManhuausCrawlerFactory().create_crawler()
    # manhuaus_crawler.crawl()
    # manhuaus_crawler.push_to_db(type='all', new=True, slug_format=False, publish=True)
    manhuaus_crawler.push_to_db(type='all', new=False, slug_format=False, publish=True)
