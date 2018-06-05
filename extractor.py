import requests
from bs4 import BeautifulSoup


class Extractor:

    def __init__(self, hostname):
        self.hostname = hostname
