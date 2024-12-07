from swarm import Agent, Swarm

from duck import search_news
from models import model_list
from prompts import *

client = Swarm()

QWEN7 = 2
LLAMA7 = 0
GPT = 10

MODEL = LLAMA7


def search_news_agent(q=None, query=None):
    """
    Accept either 'q' or 'query' parameter for search
    """
    return news_gatherer


def write_article(content=None):
    return article_writer


def publish_article(article=None):
    return publisher


news_director = Agent(
    name="NewsDirector",
    model=model_list[MODEL],
    instructions="""You are a News Director responsible for:
    1. Deciding what topics to cover
    2. Coordinating the news gathering and writing process
    3. Ensuring high-quality content
    4. Managing the publication workflow
    
    Provide clear instructions about what news to gather and what angle to take.""",
    functions=[search_news_agent, write_article, publish_article],
)

news_gatherer = Agent(
    name="NewsGatherer",
    model=model_list[MODEL],
    instructions="""You are a News Researcher who:
    1. Takes a topic or query
    2. Uses the search_news function to gather relevant information
    3. Analyzes and summarizes the findings
    4. Provides structured data for the article writer
    
    Always verify sources and collect multiple perspectives.""",
)

article_writer = Agent(
    name="ArticleWriter",
    model=model_list[MODEL],
    instructions="""You are a Professional Writer who:
    1. Takes researched information
    2. Creates engaging, well-structured articles
    3. Maintains journalistic standards
    4. Produces SEO-friendly content
    
    Write in AP style and ensure factual accuracy.""",
)

publisher = Agent(
    name="Publisher",
    model=model_list[MODEL],
    instructions="""You are a Content Publisher who:
    1. Takes the final article
    2. Formats it for WordPress
    3. Adds appropriate tags and categories
    4. Handles the publication process
    
    Ensure proper formatting and metadata.""",
)
response = client.run(
    agent=news_director,
    messages=[
        {
            "role": "user",
            "content": "Find and write an article about the latest developments in artificial intelligence.",
        }
    ],
)

print(response.messages[-1]["content"])
