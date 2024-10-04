from langchain_core.tools import tool

from langchain_community.tools import TavilySearchResults


@tool
def add(a: int, b: int):
    """Add two numbers. Please let the user know that you're adding the numbers BEFORE you call the tool"""
    return a + b

TOOLS = [add]