from urllib.parse import urlparse, urljoin
from time import sleep

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
user_agent = UserAgent()


class Site:

    def __init__(self, hostname):
        self.hostname = hostname
        self.root_url = self.get_root()
        self.headers = {'User-Agent': user_agent['google chrome']}
        self.site_urls = set()
        self.interlinking = {}
        self.sitemap_tree = {
            'index': '/sitemap_index.xml',
            'post': '/post-sitemap.xml',
            'page': '/page-sitemap.xml',
            'category': '/category-sitemap.xml'
        }

        self.get_site_urls()

    def get_interlinking(self):
        while self.site_urls:
            self.print_queue_len()
            url = self.site_urls.pop()
            print('En proceso: %s' % url)
            self.extract_page_interlink(url)

    def print_queue_len(self):
        print('URLs en cola: %d' % len(self.site_urls))

    def extract_page_interlink(self, url):
        """
        Actualmente funcionna solo para los blogs con el contenido dentro de la etiqueta 'article'
        :param url: url
        :return: Nada, guarda los enlaces y anchors en formato JSON, en la propiedad interlinking
        """
        data = {}
        text = self.make_request(url)
        soup = BeautifulSoup(text, 'lxml')
        for a in soup.article.find_all('a'):
            href = a.get('href')
            follow = a.get('rel', True)
            if href is not None and follow:
                cleaned_url = self.clean_url(href)
                if cleaned_url and cleaned_url != url:
                    anchor = a.text
                    link = cleaned_url
                    print('%s enlaza a %s con el anchor %s' % (url, link, anchor))
                    data[link] = anchor
        self.interlinking[url] = data

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

            if self.is_internal(cleaned_url):
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

    def get_site_urls(self):
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

    def goodbye(self, message='Hubo un error'):
        print('='*20)
        print(message)
        print('='*20)
        exit()


site = Site('comoquitarelmalaliento.pro')
site.get_interlinking()

print(site.interlinking)
