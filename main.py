from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pymongo
from bson.objectid import ObjectId


# FastAPI configs
app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# IPs
origins = ['*']

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB confings
mongodb_admin = "admin"
mongodb_password = "12345"
mongodb_host = "mongodb"
mongodb_port = "27017"
mongodb_connection_url = f"mongodb://{mongodb_admin}:{mongodb_password}@{mongodb_host}:{mongodb_port}"

# Connection to MongoDB
client = pymongo.MongoClient(mongodb_connection_url, serverSelectionTimeoutMS=5000)

try:
    print(client.server_info())
    print("Connected to mongodb database.")
except Exception:
    print("Unable to connect to the server.")


# Database Configs
main_database_name = "main_database"
main_collection_name = "articles"


# Databases & Collections [Creating/Checking]
databases_list = client.list_database_names()

if main_database_name in databases_list:
    print(f"The database '{main_database_name}' exists.")

    collist = client[main_database_name].list_collection_names()
    
    if main_collection_name in collist:
        print(f"The collection '{main_collection_name}' exists.")
    else:
        created_db = client[main_database_name]

        # Creating the collection
        creating_col = created_db[main_collection_name]

        # Inserting a value for creation
        default_article = {"title": "Default title", "body": "Default body", "slug": "default-article"}
        default_data = creating_col.insert_one(default_article)    
else:
    creating_db = client[main_database_name]
    creating_col = creating_db[main_collection_name]
    default_article = {"title": "Default title", "body": "Default body", "slug": "default-article"}
    default_data = creating_col.insert_one(default_article)    


# Database "main_database"
main_database = client[main_database_name]

# Collection "articles"
articles = main_database[main_collection_name]


# Home
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    articles_count = articles.count_documents({})

    context = {
        "request": request,
        "articles_count": articles_count,

    }

    return templates.TemplateResponse("home.html", context)


# Example article
@app.get("/article/test", response_class=HTMLResponse)
async def test_article(request: Request):
    return templates.TemplateResponse("article.html", {"request": request})


# Search 
@app.post('/search')
def search_query(request: Request, search_query: str = Form()):
    search_query_result = []
    how_many_results = 100

    for article in articles.find( { "$text": { "$search": str(search_query) } } ).limit(how_many_results):
        search_query_result.append(article)

    context = {
        "request": request,
        "search_query_result": search_query_result
    }

    return templates.TemplateResponse("search_result.html", context)

# Articles list
@app.get("/list/article/", response_class=HTMLResponse)
async def test_article(request: Request):

    articles_list = []
    how_many_articles = 10

    for article in articles.find().limit(how_many_articles):
        articles_list.append(article)

    context = {
        "request": request,
        "articles_list": articles_list
    }

    return templates.TemplateResponse("list_articles.html", context)


# Read article
@app.get("/article/{article_slug}", response_class=HTMLResponse)
async def read_article_by_id(request: Request, article_slug):

    article = articles.find_one({"slug": article_slug})

    related_articles_number = 3
    related_articles_list = articles.find( { "$text": { "$search": str(search_query) } } ).limit(related_articles_number)

    if article:

        context = {
            "request": request,
            "article": article,
            "related_articles_list": related_articles_list,
        }

        return templates.TemplateResponse("article.html", context)

    return templates.TemplateResponse("404.html", {"request": request})



