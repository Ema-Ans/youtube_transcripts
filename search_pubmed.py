from Bio import Entrez
import os
import json
import csv
from lxml import etree
import time
import requests
from bs4 import BeautifulSoup
import datetime

# Always provide your email address and API key to NCBI when using Entrez
Entrez.email = 'haonanhou8@gmail.com'
Entrez.api_key = 'ff10a6808d2a435879e45cd022b685e80107'

age_filter_correspondence = {
    'Newborn: birth-1 month': 'newborn[FILT]',
    'Infant: 1-23 months': 'infant[FILT]',
    'Preschool child: 2-5 years': 'preschool[FILT]',
    'Child: 6-12 years': 'child[FILT]',
    'Adolescent: 13-18 years': 'adolescent[FILT]',
    'Young adult: 19-24 years': 'young adult[FILT]',
    'Adult: 19-44 years': 'adult[FILT]',
    'Middle aged: 45-64 years': 'middle aged[FILT]',
    'Aged: 65+ years': 'aged[FILT]',
    '80 and over': '80 and over[FILT]'
}

age_indices = {
    0: 'Newborn: birth-1 month',
    1: 'Infant: 1-23 months',
    2: 'Preschool child: 2-5 years',
    3: 'Child: 6-12 years',
    4: 'Adolescent: 13-18 years',
    5: 'Young adult: 19-24 years',
    6: 'Adult: 19-44 years',
    7: 'Middle aged: 45-64 years',
    8: 'Aged: 65+ years',
    9: '80 and over'
}

def search_pubmed(keyword):
    search_term = keyword
    handle = Entrez.esearch(db='pubmed', 
                            sort='relevance', 
                            retmax='800',
                            retmode='xml', 
                            term=search_term)
    results = Entrez.read(handle)
    return results

def fetch_details(id_list, db='pubmed'):
    ids = ','.join(id_list)
    handle = Entrez.efetch(db=db,
                           retmode='xml',
                           id=ids)
    results = Entrez.read(handle)
    return results

# Include a User-Agent header to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

def get_pdf_links(pubmed_url):
    # Try to extract the PDF link from the article's PubMed page
    response = requests.get(pubmed_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Look for the link to the PDF by searching for <a> tags with text 'PDF'
        pdf_link = soup.find(lambda tag: tag.name == "a" and "PDF" in tag.text)
        
        if pdf_link and 'href' in pdf_link.attrs:
            # Construct the full URL to the PDF
            pdf_url = "https://www.ncbi.nlm.nih.gov" + pdf_link['href']
            print("Found PDF URL:", pdf_url)
            return pdf_url
        else:
            print("PDF link not found on the page.")
    else:
        print("Failed to retrieve the article page. Status code:", response.status_code)
    return None

def download_pdf(pdf_url, file_path):
    # Download the PDF from the provided URL
    try:
        response = requests.get(pdf_url, headers=headers)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Error downloading {pdf_url}: {str(e)}")
    return False

def dict_element_to_string(element):
    if isinstance(element, dict):
        # If the element is a dictionary, recursively process its items
        return ' '.join(dict_element_to_string(value) for _, value in element.items())
    elif isinstance(element, list):
        # If the element is a list, recursively process its elements
        return ' '.join(dict_element_to_string(item) for item in element)
    elif isinstance(element, str):
        # If the element is a string, return it as is
        return element
    else:
        # For all other data types, convert them to a string
        return str(element)
    
def keyword_count(keywords, text):
    count = {}
    for keyword in keywords:
        count[keyword] = text.count(keyword)
    return count

# def keyword_isin(keywords, text):
#     return any(keyword in text for keyword in keywords)

def start_search():
    print("\nWelcome to the PubMed search tool version 0.1!")
    print("\nPlease enter your search keyword(s) one by one, after each keyword, press enter. To finish adding the keywords, please press enter without any input.")
    print("\nPlease note that the keywords will be joined by AND operator. You will add the age filter in the next step.")
    original_keywords = []
    stopped = False
    while not stopped:
        keyword = input("Please enter a keyword: ")
        if keyword:
            original_keywords.append(keyword)
        else:
            stopped = True
    
    print("\nNow, please specify the age filter for the search results. Simply input the index of the age group you want to filter by. If you don't want to filter by age, please input -1.")
    print("\nThe age groups are as follows:")
    for index, age_group in age_indices.items():
        print(f"{index}: {age_group}")
    age_filter_index = int(input("Please enter the index of the age group you want to filter by: "))
    age_filter = age_filter_correspondence[age_indices[age_filter_index]] if age_filter_index != -1 else None
    keywords = original_keywords.copy()
    keywords.append(age_filter)

    # Join the keywords with AND operator, surrounded by parentheses
    keyword = "(" + ") AND (".join(keywords) + ")" + " AND (freetext[FILT])"

    print("\nSearching PubMed with the following query:", keyword)

    results = search_pubmed(keyword)

    print("\nFound articles:", results['Count'])

    # Use the ID list from the search results
    id_list = results['IdList']
    papers = fetch_details(id_list)

    directory = ('_'.join(original_keywords))
    if not os.path.exists(directory):
        os.makedirs(directory)

    paper_details = [] # Four fields: title, abstract, link, keyword count

    # Contain information of keywords in the title
    keywords_in_title = []
    keywords_in_abstract = []

    for article in papers['PubmedArticle']:
        article_ids = article['PubmedData']['ArticleIdList']
        pmid = next((str(id) for id in article_ids if id.attributes['IdType'] == 'pubmed'), None)
        pmc_id = next((str(id) for id in article_ids if id.attributes['IdType'] == 'pmc'), None)
        doi = next((str(id) for id in article_ids if id.attributes['IdType'] == 'doi'), None)
        article_title = article['MedlineCitation']['Article']['ArticleTitle']
        keywords_in_title = [kw for kw in original_keywords if kw.lower() in article_title.lower()]
        age_group = age_indices[age_filter_index]
        try:
            article_abstract = article['MedlineCitation']['Article']['Abstract']['AbstractText']
            # The abstract is a list. Let's join it into a single string
            string_article_abstract = ' '.join(article_abstract)
            keywords_in_abstract = [kw for kw in original_keywords if kw.lower() in string_article_abstract.lower()]
        except KeyError:
            article_abstract = "No abstract available."
        if pmc_id:
            try:
                handle = Entrez.efetch(db='pmc', retmode='xml', id=pmc_id)
            except Exception as e:
                print(f"Error fetching PMC ID {pmc_id}, trying again after 2 seconds...")
                time.sleep(2)
                handle = Entrez.efetch(db='pmc', retmode='xml', id=pmc_id)
            results = Entrez.read(handle, validate=False)
            result_string = dict_element_to_string(results)
            keyword_count_dict = keyword_count(original_keywords, result_string)
            paper_details.append([article_title, age_group, article_abstract, keywords_in_title, keywords_in_abstract, f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/", keyword_count_dict])
            pdf_url = get_pdf_links(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/")
            print(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/")
            if pdf_url:
                # If the article title ends with a period, remove it for the filename
                article_title = article_title.rstrip('.')
                pdf_path = f"{directory}/{article_title}.pdf"
                success = download_pdf(pdf_url, pdf_path)
                if success:
                    print(f"PDF downloaded successfully: {pdf_path}")
                else:
                    print(f"Failed to download PDF for {article_title}")
        elif doi:
            paper_details.append([article_title, age_group, article_abstract, keywords_in_title, keywords_in_abstract, f"https://doi.org/{doi}", {"placeholder": 0}])
        else:
            paper_details.append([article_title, age_group, article_abstract, keywords_in_title, keywords_in_abstract, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", {"placeholder": 0}])

    # Write the paper details to a CSV file with appropriate headers
    with open(f"papers_{keyword.replace(' ', '_')}.csv", 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Age Group", "Abstract", "Keywords in Title", "Keywords in Abstract", "Link", "Keyword Count"])
        # Sort the papers first based on the keyword count in title, then keyword count in abstract, and finally the keyword count in the full text
        paper_details.sort(key=lambda x: (sum(x[6].values()), len(x[3]), len(x[4])), reverse=True)
        for paper in paper_details:
            # If the keywords_count (paper[6]) contains "placeholder" key, it means that the full text is not available, then put "N/A" in the keyword count column
            # Otherwise, write the keyword count dictionary to the CSV file
            keyword_count_str = "N/A" if "placeholder" in paper[6] else json.dumps(paper[6])
            writer.writerow([paper[0], paper[1], paper[2], paper[3], paper[4], paper[5], keyword_count_str])
        
        
start_search()