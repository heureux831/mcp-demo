import csv
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("tasklist")

@mcp.tool()
async def get_tasklist(category: str) -> str:
    tasks = []
    with open("../tasks.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["category"] == category:
                tasks.append(row)
    return "\n".join([f"ID: {task['id']} | Task: {task['task_name']} | Category: {task['category']} | Priority: {task['priority']} | Status: {task['status']} | Deadline: {task['deadline']} | Assignee: {task['assignee']}"for task in tasks])

if __name__ == "__main__":
    # Initialize and run the server
    print("Starting tasklist server...")
    mcp.run(transport='stdio')