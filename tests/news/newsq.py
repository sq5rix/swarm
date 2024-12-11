import logging
import time

from duck import search_news
from models import model_list
from prompts import *

from swarm import Agent, SwarmRabbitMQ

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("NewsAgents")

# Initialize SwarmRabbitMQ client
client = SwarmRabbitMQ()

QWEN7 = 2
LLAMA7 = 0
GPT = 10
MODEL = LLAMA7

# Define the worker agents
news_gatherer = Agent(
    name="NewsGatherer",
    model=model_list[MODEL],
    instructions="""You are a News Researcher who:
    1. Takes a topic or query
    2. Uses the search_news function to gather relevant information
    3. Analyzes and summarizes the findings
    4. Provides structured data for the article writer
    
    Always verify sources and collect multiple perspectives.""",
    functions=[search_news],
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

# Register agents with the client
logger.info("Registering agents...")
client.register_agent(news_gatherer)
logger.info(f"Agent {news_gatherer.name} registered")
client.register_agent(article_writer)
logger.info(f"Agent {article_writer.name} registered")
client.register_agent(publisher)
logger.info(f"Agent {publisher.name} registered")


if __name__ == "__main__":
    print("\nStarting News Agents System...")
    print("Waiting for tasks. Press Ctrl+C to exit.\n")

    try:
        while True:
            # Check for messages in the queue
            for agent in [news_gatherer, article_writer, publisher]:
                try:
                    # Try to get a message from the queue
                    message = client.receive_message(agent.name)
                    if message:
                        print(f"\n{'='*50}")
                        print(f"Message received for {agent.name}:")
                        print(f"Content: {message[:200]}...")
                        print(f"{'='*50}")

                        # Process the message
                        response = client.run(
                            agent=agent, messages=[{"role": "user", "content": message}]
                        )

                        print(f"\nResponse from {agent.name}:")
                        print(f"{'='*50}")
                        print(response.messages[-1]["content"][:200])
                        print(f"{'='*50}\n")
                except Exception as e:
                    if "no attribute 'receive_message'" not in str(e):
                        print(f"Error processing messages for {agent.name}: {e}")

            time.sleep(1)  # Wait a second before checking again

    except KeyboardInterrupt:
        print("\nShutting down workers...")
        client.close()
