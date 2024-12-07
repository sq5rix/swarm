from duckduckgo_search import DDGS


def search_news(query, max_results=5):
    """
    Search for news articles using DuckDuckGo
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(keywords=query, max_results=max_results))
            return [
                {
                    "title": result["title"],
                    "link": result["link"],
                    "snippet": result["body"],
                }
                for result in results
            ]
    except Exception as e:
        return f"Error searching news: {str(e)}"
