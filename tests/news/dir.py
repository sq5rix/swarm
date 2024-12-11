import logging

from duck import search_news
from models import model_list
from newsq import article_writer, news_gatherer, publisher
from prompts import *

from swarm import Agent, SwarmRabbitMQ

# Configure minimal logging
logging.basicConfig(level=logging.WARNING)

# Initialize SwarmRabbitMQ client
client = SwarmRabbitMQ()

QWEN7 = 2
LLAMA7 = 0
GPT = 10
MODEL = LLAMA7

print("\n=== News Director AI System ===")
print("Type 'quit' to exit\n")


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


def main():
    while True:
        try:
            # Get user input
            user_input = input("\nWhat news topic should I cover? > ")

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nShutting down News Director...")
                break

            # Send task to the news pipeline
            print("\nProcessing request...")
            response = client.run(
                agent=news_director,
                messages=[
                    {
                        "role": "user",
                        "content": user_input,
                    }
                ],
            )

            print("\nDirector's Response:")
            print("-" * 40)
            print(response.messages[-1]["content"])
            print("-" * 40)

        except KeyboardInterrupt:
            print("\nShutting down News Director...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()
