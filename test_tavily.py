
import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError("TAVILY_API_KEY is missing from .env")

client = TavilyClient(api_key=api_key)

response = client.search(
    query="Applications of artificial intelligence in healthcare",
    search_depth="basic",
    max_results=5,
)
# print(response)
# for index, result in enumerate(response["results"], start=1):
#     print(f"\nSource {index}")
#     print("Title:", result.get("title"))
#     print("URL:", result.get("url"))
#     print("Summary:", result.get("content"))
#     print("Relevance:", result.get("score"))

urls = [
    result["url"]
    for result in response["results"][:3]
    if result.get("url")
]

if urls:
    extracted = client.extract(
        urls=urls,
        format="markdown",
    )

    for page in extracted["results"]:
        print("\nURL:", page["url"])
        print("Content:")
        print((page.get("raw_content") or "")[:3000])
