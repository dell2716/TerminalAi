# TerminalAi
# DeepSeekTerminal

> Graphical Terminal Chat with DeepSeek AI  
> 与 DeepSeek AI 终端聊天图形化界面

---

## Features • 功能概览

| Feature                                       | Description                                                                                       | 功能                 | 说明                                                             |
|-----------------------------------------------|---------------------------------------------------------------------------------------------------|----------------------|------------------------------------------------------------------|
| Graphical UI                                  | Built with Rich + Textual: input box, buttons, sidebar, scroll areas                              | 图形化终端界面       | 使用 Rich + Textual 实现，支持输入框、按钮、侧边栏、滚动区域等   |
| Chat History                                  | Auto‑save chats as JSON; view/load/delete sessions                                                | 聊天历史管理         | 每个聊天自动保存为 JSON 文件，可查看、加载、删除                 |
| Markdown Rendering                            | AI replies rendered with Markdown (formats, code blocks…)                                         | Markdown 渲染        | AI 回复使用 Markdown 高亮展示，支持格式、代码块等               |
| API Integration                               | Connect to DeepSeek API; API key configurable & savable                                           | API 接入             | 接入 DeepSeek 官方 API, 可配置 API 密钥，支持保存               |
| Keyboard Shortcuts                            | Ctrl+N new chat, Ctrl+D delete chat, Ctrl+Q quit                                                  | 键盘快捷操作         | 支持 Ctrl+N 新建、Ctrl+D 删除聊天，Ctrl+Q 退出                  |
| Async Handling                                | Non‑blocking async requests to keep UI responsive                                                  | 异步处理             | 异步请求发送/接收，防止界面卡顿                                 |

---

## Installation • 安装

1. **Clone the repo**  
   克隆仓库  
   ```bash
   git clone https://github.com/<your-username>/DeepSeekTerminal.git
   cd DeepSeekTerminal
Create & activate virtual env
创建并激活虚拟环境

bash
复制
编辑
python3 -m venv venv
source venv/bin/activate
Install dependencies
安装依赖

bash
复制
编辑
pip install -r requirements.txt
Configuration • 配置
Obtain your DeepSeek API key
获取 DeepSeek API Key
Log in to DeepSeek Platform, copy the key starting with sk-....
登录 DeepSeek 平台，复制以 sk-... 开头的 API 密钥。

Set env var or input on first launch
设置环境变量或首次运行时输入

bash
复制
编辑
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxx"
Usage • 使用
bash
复制
编辑
python main.py
On start, a new chat session is created automatically.
启动后界面会自动创建一个新聊天会话。

Type a message and press Enter or click “Send”.
在输入框输入消息，按回车或点击“发送”。

Use sidebar to load or delete past chats.
浏览侧边栏聊天列表，可加载或删除历史会话。

Key Bindings • 快捷键
Action	Windows / Linux	macOS	功能
New chat	Ctrl + N	⌘ + N	新建聊天
Delete current chat	Ctrl + D	⌘ + D	删除当前聊天
Quit application	Ctrl + Q	⌘ + Q	退出应用

Contributing • 贡献
Fork this repo
Fork 本仓库

Create a branch feature/YourFeature
创建分支 feature/YourFeature

Commit your changes
提交修改

Open a Pull Request
发起 Pull Request
