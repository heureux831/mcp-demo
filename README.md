## The simplest mcp project
本项目实现了最小的mcp项目，方便理解整个MCP系统的运行，

项目使用了deepseek的api_key,请在.env文件中添加你的api_key

如果使用其他LLM服务，请在env文件中添加相应的API_KEY，请选择支持MCP服务的LLM服务

## 文件结构

```
├── .env
├── .gitignore
├── client/client.py
├── client/server.json
├── server/tasklist.py
├── pyproject.toml
|── tasks.csv   
|── README.md

```

### 创建虚拟环境
```shell
uv venv

# Activate virtual environment

# On Windows:
.venv\Scripts\activate

# On Unix or MacOS:
source .venv/bin/activate
```
### 安装依赖
```shell
## 使用openai格式来访问
uv add mcp openai python-dotenv
```

### 创建.env文件
```shell
touch .env
```
# Add API key to .env file
```shell
echo "OPENAI_API_KEY=your_api_key" >> .env
echo "OPENAI_BASE_URL="https://api.deepseek.com/v1"" >> .env
echo "OPENAI_MODEL="deepseek-chat" >> .env
```
### 编辑server.json文件来指定mcp-server

```json
{
    "servers": [
      {
        "command": "uv",
        "args": ["run","../server/tasklist.py"],
        "env": null
      },
      {
        "command": "uv",
        "args": ["run","../server/weather.py"],
        "env": null
      },
      {
        "command": "npx",
        "args": ["-y","../server/stock.js"],
        "env": null
      }
    ]
  }
```

### 运行mcp-demo
```shell
cd client
uv run client.py server.json
```

然后输入用户query即可