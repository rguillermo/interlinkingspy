from urllib.parse import urlparse, urljoin
from time import sleep

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
user_agent = UserAgent()


class Extractor:

    def __init__(self, hostname):
        self.hostname = hostname
        self.root_url = self.get_root()
        self.headers = {'User-Agent': user_agent['google chrome']}
        self.site_urls = set()
        self.queue = self.get_seeds()
        self.sitemap_tree = {
            'index': '/sitemap_index.xml',
            'post': '/post-sitemap.xml',
            'page': '/page-sitemap.xml',
            'category': '/category-sitemap.xml'
        }

    def extract_by_sitemap(self):
        sitemap_url = urljoin(self.root_url, self.sitemap_tree['index'])
        text = self.make_request(sitemap_url)
        self.get_sitemap_urls(text)

    def get_sitemap_urls(self, text):
        sitemaps = []

        soup = BeautifulSoup(text, 'lxml')
        for sm in soup.find_all('loc'):
            path = urlparse(sm.text).path

            if path == self.sitemap_tree['post']:
                sitemaps.append(sm.text)
            elif path == self.sitemap_tree['page']:
                sitemaps.append(sm.text)
            elif path == self.sitemap_tree['category']:
                sitemaps.append(sm.text)

        self.parse_sitemaps(sitemaps)

    def parse_sitemaps(self, sitemaps):
        for url in sitemaps:
            r = requests.get(url)
            s = BeautifulSoup(r.text, 'lxml')
            loc = s.find_all('loc')
            for link in loc:
                if link.text not in self.site_urls and link.text.rstrip('/') not in self.site_urls:
                    self.site_urls.add(link.text)

    def extract_by_follow_links(self):
        while self.queue:
            self.print_queue_len()
            url = self.queue.pop()
            self.site_urls.add(url)
            urls = self.extract_links(url)
            self.queue = self.queue.union(urls)
            sleep(2)

    def print_queue_len(self):
        print('URLs en cola: %d' % len(self.queue))

    def get_seeds(self):
        return self.extract_links(self.root_url)

    def extract_links(self, url):
        url_list = []
        text = self.make_request(url)
        soup = BeautifulSoup(text, 'lxml')
        for a in soup.find_all('a'):
            href = a.get('href')
            if href is not None:
                cleaned_url = self.clean_url(href)
                if cleaned_url:
                    url_list.append(cleaned_url)
        return set(url_list)

    def is_internal(self, url):
        url_parts = urlparse(url)
        if self.hostname == url_parts.netloc:
            return True
        else:
            return False

    def clean_url(self, url):
        url_parts = urlparse(url)
        if url_parts.scheme and url_parts.netloc:
            cleaned_url = '{scheme}://{netloc}{path}'.format(
                scheme=url_parts.scheme, netloc=url_parts.netloc, path=url_parts.path
            )

            if self.is_internal(cleaned_url) and cleaned_url not in self.site_urls:
                return cleaned_url

    def get_root(self):
        return 'http://{hostname}'.format(hostname=self.hostname)

    def make_request(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.text
            else:
                self.goodbye('HTTP: %d' % response.status_code)
        except requests.exceptions.ConnectionError:
            self.goodbye('Hubo un error mientras se solicitada la pagina web...')

    def goodbye(self, message='Hubo un error'):
        print('='*20)
        print(message)
        print('='*20)
        exit()

