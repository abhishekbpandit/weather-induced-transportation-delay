import ast
import requests
import langchain_core
import concurrent.futures
import pandas as pd
from bs4 import BeautifulSoup as Soup
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from serpapi import GoogleSearch
from datetime import datetime, timedelta

# URL of your Flask app for processing articles
PROCESS_ARTICLE_URL = "https://a9cf-35-243-113-176.ngrok-free.app/process_article"

def average(lst): 
    """Calculate the average of a list."""
    return sum(lst) / len(lst) if lst else 0

def create_query(source, destination):
    """Create a search query for flight delay information."""
    return f'{source.split(",")[0]} {destination.split(",")[0]} flight delay'

def remove_nav_and_header_elements(page):
    """Remove navigation, header, and footer elements from a webpage."""
    content = Soup(page, 'html.parser')
    for element in content.find_all(["nav", "footer", "header", "head"]):
        element.decompose()
    return str(content.text).strip()

def fetch_articles(url):
    """Fetch articles from a given URL."""
    try:
        loader = RecursiveUrlLoader(url=url, max_depth=1, extractor=remove_nav_and_header_elements)
        doc = loader.load()
        return doc[0] if doc else ""
    except Exception as e:
        return str(e)

def fetch_articles_for_query(query, departure_date):
    """Fetch articles related to a query within a specified date range."""
    end_date = departure_date
    start_date = end_date - timedelta(days=1)
    results = search_with_date_filter(query, start_date, end_date)
    urls = [x['link'] for x in results if 'pdf' not in x['link']]
    articles = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_articles, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            article = future.result()
            if isinstance(article, langchain_core.documents.base.Document):
                if not ('403 Forbidden' in article.metadata['title'] or 'Error' in article.metadata['title']):
                    articles.append(article.page_content)
    return articles

def search_with_date_filter(query, start_date, end_date):
    """Perform a search using SERP API with date filters."""
    api_key = "3be86335905bfda27c9bd8e81b6b1c7147d6df2369c0db6139688f2ed3d75344"
    start_date_str = start_date.strftime('%m/%d/%Y')
    end_date_str = end_date.strftime('%m/%d/%Y')

    params = {
        'engine': 'google_news',
        'api_key': api_key,
        'q': query,
        'tbs': f'cdr:1,cd_min:{start_date_str},cd_max:{end_date_str}'
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    return [result for result in results.get("news_results", []) if start_date <= datetime.strptime(result['date'].split(',')[0], '%m/%d/%Y').date() <= end_date]

def get_delay(articles, source, destination):
    """Get delay information by sending articles to a Flask app for processing."""
    data = {
        'articles': articles,
        'source': source,
        'destination': destination
    }
    response = requests.post(PROCESS_ARTICLE_URL, json=data)
    if response.status_code == 200:
        return response.json().get('entities', [])
    else:
        return []

def estimate_delay_nlp(source, destination, departure_date):
    """Estimate delay using NLP on fetched articles."""
    query = create_query(source, destination)
    articles = fetch_articles_for_query(query, departure_date)
    if articles:
        delay_list = get_delay(articles, source, destination)
        print("Extracted Delays:", delay_list)
        delay = average(delay_list)
    else:
        delay = 0

    return timedelta(minutes=delay)
