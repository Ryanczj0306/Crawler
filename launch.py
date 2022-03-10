from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler
import scraper

def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    crawler.start()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)
    print("***************************************")
    print("***************************************")
    print("***************************************")
    
    print(scraper.longest_page)
    print(scraper.longest_url)
    print(len(scraper.urlSet))
    
    print(sorted(scraper.word_freq.items(), key = lambda x : x[1], reverse = True)[:50])
    
    print(scraper.uci_count)
    print(sorted(scraper.subdomains.items(), key = lambda x : x[1], reverse = True))
