"""
Tools package initializer.

This file imports all tools defined in this package and provides a single
list `ALL_TOOLS` that can be passed directly to your LLM via bind_tools().
"""

from utils.tools.Mongo_Tool import retrieve_memories,save_memory  # Your memory tools
from utils.tools.Addition import add  # Your math tool
# from .nlp import extract_entities  # Example: if you have an NLP tool

# Collect all tools in a single list
ALL_TOOLS = [retrieve_memories,save_memory,add]
