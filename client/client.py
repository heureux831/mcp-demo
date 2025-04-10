import asyncio
import json
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
        self.model = os.getenv("OPENAI_MODEL")

    async def connect_to_servers(self, config_file_path: str):
        """Connect to MCP servers based on the configuration in a JSON file

        Args:
            config_file_path: Path to the JSON configuration file
        """
        try:
            with open(config_file_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {config_file_path} not found")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")

        servers = config.get("servers", [])
        if not servers:
            raise ValueError("Configuration file must contain a 'servers' array")

        for server in servers:
            command = server.get("command")
            args = server.get("args", [])
            env = server.get("env", None)

            if not command:
                raise ValueError("Each server configuration must have a 'command'")

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(
                    StdioServerParameters(
                        command=command,
                        args=args,
                        env=env
                    )
                )
            )
            stdio, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
            self.sessions.append(session)

            await session.initialize()

            # List available tools for this server
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to server {command} {args} with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using OPENAI and available tools from all connected servers"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        # Collect tools from all connected servers
        all_tools = []
        for session in self.sessions:
            response = await session.list_tools()
            tools = response.tools
            all_tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                } for tool in tools
            ])

        # Initial OPENAI API call
        response = self.openai.chat.completions.create(
            model=self.model,
            max_tokens=1000,
            messages=messages,
            tools=all_tools
        )

        # Process response and handle tool calls
        content = response.choices[0]
        if content.finish_reason == "tool_calls":
            # If a tool call is needed, parse the tool
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # Find the session that has the tool
            tool_session = None
            for session in self.sessions:
                tools = (await session.list_tools()).tools
                if any(tool.name == tool_name for tool in tools):
                    tool_session = session
                    break

            if tool_session is None:
                raise ValueError(f"Tool {tool_name} not found in any connected server")

            # Execute the tool
            result = await tool_session.call_tool(tool_name, tool_args)
            print(f"\n\n[Calling tool {tool_name} with args {tool_args}]\n\n")

            # Append the tool call and result to messages
            messages.append(content.message.model_dump())
            messages.append({
                "role": "tool",
                "content": result.content[0].text,
                "tool_call_id": tool_call.id,
            })
            print(result.content[0].text)

            # Send the result back to the model for the final response
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return response.choices[0].message.content

        return content.message.content

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_config_file>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_servers(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())