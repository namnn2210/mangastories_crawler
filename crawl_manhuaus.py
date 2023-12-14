from scrapers.manhuaus import ManhuausCrawlerFactory

if __name__ == "__main__":
    manhuaus_crawler = ManhuausCrawlerFactory().create_crawler()
    manhuaus_crawler.crawl()
