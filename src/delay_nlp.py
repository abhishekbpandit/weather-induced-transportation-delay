import ast
import requests
import langchain_core
import concurrent.futures
import pandas as pd
from bs4 import BeautifulSoup as Soup
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from serpapi import GoogleSearch
from datetime import datetime, timedelta

# URL of your Flask app
url = "https://9d22-35-243-113-176.ngrok-free.app/process_article"


def Average(lst): 
    if len(lst) > 0:
        return sum(lst) / len(lst) 
    return 0

def create_query(source, destination):
    return f'{source.split(",")[0]} {destination.split(",")[0]} flight delay'

def remove_nav_and_header_elements(page):
    content = Soup(page, 'html.parser')
    exclude = content.find_all(["nav", "footer", "header", "head"])
    for element in exclude:
        element.decompose()

    return str(content.text).strip()

def fetch_articles(url):
    try:
        loader = RecursiveUrlLoader(
            url=url, max_depth=1, extractor=remove_nav_and_header_elements
        )
        doc = loader.load()
        return doc[0] if doc else ""
    except Exception as e:
        return str(e)

def fetch_articles_for_query(query, departure_date):
    end_date = departure_date
    start_date = end_date - timedelta(days=1)

    results = search_with_date_filter(query, start_date, end_date)
    urls = [x['link'] for x in results if 'pdf' not in x['link']]
    articles = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_articles, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            article = future.result()
            if type(article) == langchain_core.documents.base.Document:
                if not ('403 Forbidden' in article.metadata['title'] or 'Error' in article.metadata['title']):
                    articles.append(article.page_content)
    return articles


def search_with_date_filter(query, start_date, end_date):
    """
    Perform a search using a SERP API with date filters.

    Args:
    query (str): The search query.
    start_date (datetime.date): The start date for filtering results.
    end_date (datetime.date): The end date for filtering results.
    api_key (str): Your API key for the SERP API service.

    Returns:
    dict: The search results returned by the API.
    """
    api_key = "3be86335905bfda27c9bd8e81b6b1c7147d6df2369c0db6139688f2ed3d75344"
    # Format dates in the required format, e.g., YYYY-MM-DD
    start_date_str = start_date.strftime('%m/%d/%Y')
    end_date_str = end_date.strftime('%m/%d/%Y')

    # Define the parameters for the API request
    params = {
        'engine': 'google_news',
        'api_key': api_key,
        'q': query,
        'tbs': f'cdr:1,cd_min:{start_date_str},cd_max:{end_date_str}'
        # Add other parameters as required by your specific SERP API
    }

    # Make the API request
    search = GoogleSearch(params)
    results = search.get_dict()
    if results and 'news_results' in results.keys(): 
        #print([(start_date,datetime.strptime(result['date'].split(',')[0], '%m/%d/%Y').date(),end_date) for result in results["news_results"]])
        #print([result for result in results["news_results"] if start_date <= datetime.strptime(result['date'].split(',')[0], '%m/%d/%Y').date() <= end_date])
        return [result for result in results["news_results"] if start_date <= datetime.strptime(result['date'].split(',')[0], '%m/%d/%Y').date() <= end_date]
    else:
        return []



def get_delay(articles, source, destination):
    url = 'https://a9cf-35-243-113-176.ngrok-free.app/process_article'
    data = {}
    data['articles'] = articles
    data['source'] = source
    data['destination'] = destination
    # Making a POST request
    response = requests.post(url, json=data)

    # Checking the response
    if response.status_code == 200:
        return response.json()['entities']
    else:
        return []

def estimate_delay_nlp(source, destination, departure_date):
    query = create_query(source, destination)
    articles = fetch_articles_for_query(query, departure_date)
    if len(articles) > 0:
        delay_list = get_delay(articles, source, destination)
        print(delay_list)
        delay = float(Average(delay_list))
    else:
        delay = float(0)
    
    return timedelta(minutes=float(delay))
