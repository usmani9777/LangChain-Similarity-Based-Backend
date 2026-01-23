from langchain.tools import tool

@tool
def add(a: int, b: int) -> int:
    """
    Add two integers asynchronously.

    This tool takes two integers as input and returns their sum. 
    Can be used by an LLM to perform simple arithmetic operations.

    Args:
        a (int): The first number to add.
        b (int): The second number to add.

    Returns:
        int: The sum of a and b.

    Example:
        >>> result = await add(5, 7)
        >>> print(result)
        12
    """
    return a + b


