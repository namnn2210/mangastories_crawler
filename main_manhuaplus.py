from scrapers.manhuaplus import ManhuaplusCrawlerFactory

if __name__ == "__main__":
    ManhuaplusCrawlerFactory().create_crawler().crawl()
