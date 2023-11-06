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
from imdb_helper_functions import prep_actor_soup, prep_cast_page_soup, filmo_category_section_finder, get_actor_name

def get_actors_by_movie_soup(cast_page_soup:BeautifulSoup(), num_of_actors_limit=None) -> list():
    """
    This function takes a beautifulsoup soup object (cast_page_soup) of a page for the cast & crew for the current film.
    params:
        cast_page_soup: soup object of a page for the cast & crew for the current film
        num_of_actors_limit: int, optional, default=None
    return:
        actors: list of tuples (name_of_actor, url_to_actor_page)
    """
    cast_table = cast_page_soup.find_all('table', class_ = 'cast_list')
    actors = [(i.text.strip(), 'https://www.imdb.com' + i.find('a')['href']) for i in cast_table[0].find_all('td', attrs={'class' : None})]
    match = re.compile(r'\?.*')
    actors = [(i[0], re.sub(match, 'fullcredits', i[1])) for i in actors]
    
    if num_of_actors_limit is not None:
        actors = actors[:num_of_actors_limit]
    return actors


def get_movies_by_actor_soup(actor_page_soup:BeautifulSoup(), num_of_movies_limit=None) -> list():
    """
    This functions takes a beautifulsoup soup object (actor_page_soup) of the actors page and returns a list of all movies that the actor played in.
    params:
        actor_page_soup: soup object of the actors fullcredits page on IMDB
        num_of_movies_limit: int, optional, default=None, limit the number of movies returned
    returns:
        films_and_links: list of tuples (name_of_movie, url_to_movie_page)
    """
    # find all instances where the person was an actor
    index = filmo_category_section_finder(actor_page_soup)
    is_actor = actor_page_soup.find_all('div', class_='filmo-category-section')[index]

    # find all movies
    content = is_actor.find_all('div', class_ = 'filmo-row')

    # find all movies that have already been released - a safe check
    movies_w_year = [i for i in content if i.find('span', class_= 'year_column').text.strip() not in ['????', '']]

    # remove unreleased
    released_movies = [i for i in movies_w_year if i.find('a', attrs={'class': 'in_production'}) is None]

    # list of content types to exclude
    exclude_list = ['(TV Series)', '(Short)', '(Video Game)', '(Video documentary)', '(Video documentary short)', '(Video short)', '(Video)', '(TV Movie)', '(TV Mini Series)', '(TV Mini-Series)', '(TV Series short)', '(TV Series documentary)', '(TV Special)', '(Music Video)', '(Music Video short)', '(voice)']

    # filter the item out if it contains content other than film
    movies = [i for i in released_movies if i.contents[4].strip() not in exclude_list]

    # filter out voice overs
    movies_wo_voiceovers = [i for i in movies if exclude_list[-1] not in i.text.strip()]

    # create a tuple of format (film_name, film_url)
    films_and_links = [(i.contents[3].text.strip(), 'https://www.imdb.com' + i.find('a').attrs['href']) for i in movies_wo_voiceovers]
    films_and_links = [(i[0], re.sub(r'\?.*', 'fullcredits', i[1])) for i in films_and_links]

    
    # limit condition
    if num_of_movies_limit is not None:
        return films_and_links[:num_of_movies_limit]

    return films_and_links


def get_movie_distance(actor_start_url:str, actor_end_url:str, num_of_actors_limit=None, num_of_movies_limit=None) -> int:
    """
    This function takes two urls to actors pages and returns the movie distance between them.
    params:
        actor_start_url: url to the first actor page
        actor_end_url: url to the second actor page
        num_of_actors_limit: int, optional, default=None, limit the number of actors returned
        num_of_movies_limit: int, optional, default=None, limit the number of movies returned
    returns:
        movie_distance: int, the movie distance between the two actors when the distance is less or equal to 3, else -1
    """
    if not actor_start_url.startswith('https://www.'):
        actor_start_url = 'https://www.' + actor_start_url
    if not actor_end_url.startswith('https://www.'):
        actor_end_url = 'https://www.' + actor_end_url

    # init basic params for the search, increment distance
    curr_dist = 1
    movies_seen = set()
    actors_seen = set(actor_start_url)
    actors_to_check = [actor_start_url]

    while curr_dist <= 3: 
        tb_explored = []
        print(f'Iteration: {curr_dist}. Actors to check: {len(actors_to_check)}')

        # iterate over actors, parse movies by actor
        for actor_url in actors_to_check:
            movies = get_movies_by_actor_soup(prep_actor_soup(actor_url), num_of_movies_limit)
            movies = [m for m in movies if m[1] not in movies_seen]  #filtering out movies that have already been parsed

            # iterate over movies
            for movie in movies:
                title, link = movie
                movies_seen.add(link)  #cache movies 
                
                try:
                    actors = get_actors_by_movie_soup(prep_cast_page_soup(link), num_of_actors_limit)
                except:
                    continue
                
                #filtering out actors that have already been seen
                actors = [a for a in actors if a[1] not in actors_seen] 

                for _, actor_url in actors:
                    if actor_url == actor_end_url:
                        return curr_dist
                    
                    if actor_url not in actors_seen:
                        tb_explored.append(actor_url) 
        
        actors_seen.update(actors_to_check)
        actors_to_check = tb_explored
        curr_dist += 1
    return -1


def get_movie_descriptions_by_actor_soup(actor_page_soup: BeautifulSoup) -> list[str]:
    """
    Returns a movie description for each movie the actor has been in
    params:
        actor_page_soup: BeautifulSoup object, the actor page soup
    returns:
        descriptions: list[str], a list of movie descriptions
    """
    user_agent = {'User-agent': 'Mozilla 5.0'}
    descriptions = []

    movies = get_movies_by_actor_soup(actor_page_soup)

    for name, url in movies:
        url = url.replace('/fullcredits', '')
        response = requests.get(url, headers=user_agent)
        soup = BeautifulSoup(response.text)
        desc = soup.find('span', {'data-testid': 'plot-xl', 'role': 'presentation'})
        if desc:
            descriptions.append(desc.text.strip())
    return descriptions