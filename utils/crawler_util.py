from bs4 import BeautifulSoup
from urllib.request import Request, urlopen


def get_soup(url, header):
    return BeautifulSoup(urlopen(Request(url=url, headers=header)), 'html.parser')
