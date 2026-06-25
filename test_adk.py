import os
os.environ["GEMINI_API_KEY"] = "dummy"

try:
    from google.adk import Agent
    print("Agent imported from google.adk")
except ImportError:
    print("Could not import Agent from google.adk")

try:
    from google.adk.agents import Agent
    print("Agent imported from google.adk.agents")
except ImportError:
    pass

def my_tool(x: int) -> int:
    """Multiplies by 2.
    Args: x (int): input
    """
    return x * 2

agent = Agent(name="test", tools=[my_tool])
print(dir(agent))
