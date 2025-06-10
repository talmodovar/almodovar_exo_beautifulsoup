
import requests
from bs4 import BeautifulSoup
import re
from pymongo import MongoClient

#Pour tester avec un seul article = True, sinon false pour scrap à l'infini (mais fini par crash)
def scrape_articles(url, Test=False):
    # Connexion à MongoDB (ici en local, par défaut sur port 27017)
    client = MongoClient("mongodb://localhost:27017/")
    db = client["BlogDuModerateur"]  
    collection = db["articles"]        

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find('main').find_all('article')
    #Présent juste pour des tests en interne, plus facile d'utilisation
    if Test:
        articles = [articles[0]] if articles else []

    for article in articles:
        img = article.find('img')
        thumbnail = img['data-lazy-src'] if img else None
        
        meta = article.find('div', class_='entry-meta')
        subcategory = meta.find('span', class_='favtag').get_text().strip()
        date = meta.find('span', class_='posted-on').get_text().strip()
        
        a_tag = meta.find('a')
        title = a_tag.find('h3').get_text().strip()
        article_url = a_tag['href']
        
        summary = meta.find('div', class_='entry-excerpt').get_text().strip()
        
        article_response = requests.get(article_url, headers=headers)
        article_soup = BeautifulSoup(article_response.text, 'html.parser')
        
         # Auteur
        for a in article_soup.find_all('a', href=True):
         if "/auteur/" in a['href']:
             auteur2 = a.get_text().strip()
             break
        
        content_div = article_soup.find('div', class_='entry-content')
        content = content_div.get_text().strip() if content_div else None
        
        date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date.lower())
        if date_match:
            day, month, year = date_match.groups()
            months = {'janvier':'01','février':'02','mars':'03','avril':'04','mai':'05','juin':'06',
                     'juillet':'07','août':'08','septembre':'09','octobre':'10','novembre':'11','décembre':'12'}
            format_date = f"{year}{months.get(month,'01')}{day.zfill(2)}"
        else:
            format_date = date
        
        images = {}
        if content_div:
            for i, img in enumerate(content_div.find_all('img'), 1):
                img_url = img.get('src') or img.get('data-lazy-src')
                if not img_url or img_url.startswith("data:image"):
                    continue
                caption = img.get('alt', '') or img.get('title', '')
                images[f'image_{i}'] = {'url': img_url, 'caption': caption}
        
        # Préparer le document MongoDB
        format_date = f"{format_date[:4]}-{format_date[4:6]}-{format_date[6:]}"

        article_doc = {
            "title": title,
            "thumbnail": thumbnail,
            "subcategory": subcategory,
            "summary": summary,
            
            "date": format_date,
            "author": auteur2,
            "content": content,
            "images": images,
            "url": article_url
        }
        
        # Insérer dans MongoDB
        collection.insert_one(article_doc)
        print(f"Article '{title}' inséré dans MongoDB.")

# Utilisation
scrape_articles("https://www.blogdumoderateur.com/web/", Test=False)
