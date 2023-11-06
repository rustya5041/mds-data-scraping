import bs4
from bs4 import BeautifulSoup
import requests
import regex as re
import csv
import pandas as pd
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import networkx as nx
import os

def filmo_category_section_finder(soup):
    item_length = len(soup.find_all(class_='filmo-category-section'))
    it = 0

    for i in range(item_length):
        actor_finder = soup.find_all(class_='filmo-category-section')[i]
        for el in actor_finder.select('div'):
            if el.get('id') is not None:
                if el.get('id').split('-')[0] in ('actor', 'actress'):
                    it = i
    return it

def get_actor_name(url):
    """
    This function takes a url to a movie page and returns the title of the page - which is Actor's name. Helper function for validation
    params: url - url to a movie page
    returns: title - title of the movie
    """
    user_agent = {'User-agent': 'Mozilla 5.0'}
    fc = '/fullcredits'
    if fc in url:
        url = re.sub(fc, '', url)
    response = requests.get(url, headers=user_agent)
    title = re.search(r'<title>(.*) - IMDb</title>', response.text).group(1)
    return title

def prep_actor_soup(url:str) -> BeautifulSoup():
    """
    This function takes a url to a movie page and returns a beautifulsoup soup object of the fullcredits page.
    params: url - url to a movie page
    return: soup - beautifulsoup soup object of the fullcredits page
    """
    user_agent = {'User-agent': 'Mozilla 5.0'}
    fc = '/fullcredits'
    
    if fc in url:
        response = requests.get(url, headers=user_agent)
    else:
        response = requests.get(url+fc, headers=user_agent)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def prep_cast_page_soup(url) -> BeautifulSoup():
    """
    This function takes a url to a movie page and returns a beautifulsoup soup object of the fullcredits page.
    params: url - url to a movie page
    returns: soup - beautifulsoup soup object of the fullcredits page
    """
    user_agent = {'User-agent': 'Mozilla 5.0'}
    response = requests.get(url, headers=user_agent)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup