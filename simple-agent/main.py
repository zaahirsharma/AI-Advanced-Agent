# Connect to mcp server
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
# Prebuilt agent framework from langgraph
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

# Setting up OpenAI llm with model and API key
model = ChatOpenAI(model="gpt-4.1", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))


# Connect to FireCrawl MCP server
# Run background process, runs firecrawl-mcp client that connect to server
# Python communicates using standard input/output (Stdio) to trigger tools to get results
server_params = StdioServerParameters(
    command = "npx",
    env={
        "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY"),
    },
    args = ["firecrawl-mcp"]
)

# Connect to MCP client
async def main():
    # Can read from client (get result of agent)
    # Can write to client (using tools)
    async with stdio_client(server_params) as (read, write):
        # Connect to client with new session, ability to read and write
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Find all tools available in session and use
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)
            
            # Prompt for agent
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that can scrape websites, crawl pages, and extract data using Firecrawl tools. Think step by step and use the appropriate tools to help the user."
                }
            ]
            
            # Get and print all tools from the tools list (* unpacks these values into individual arguments)
            print("Available tools: ", *[tool.name for tool in tools])
            print("-" * 60)
            
            # Keep communicating with the agent
            while True:
                user_input = input("\nYou: ")
                if user_input == "quit":
                    print("Exiting...")
                    break
                
                # Invoke llm after with new user message, limit to 175000 characters
                messages.append({"role": "user", "content": user_input[:175000]})
                
                # Call agent
                # ainvoke is an async invocation, wait for invoke to finish
                try:
                    # Passing through state of messages to the agent
                    agent_response = await agent.ainvoke({"messages": messages})
                    ai_message = agent_response["messages"][-1].content
                    print("\nAgent:", ai_message)
                except Exception as e:
                    print("\nError:", str(e))
                    
                    
                    
if __name__ == "__main__":
    asyncio.run(main())
        