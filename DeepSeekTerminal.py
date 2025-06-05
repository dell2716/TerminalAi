"""
            🧠 项目名称: DeepSeekTerminal
📌 功能概览
功能	           说明
✅ 图形化终端界面	使用 Rich + Textual 实现，支持输入框、按钮、侧边栏、滚动区域等
✅ 聊天历史管理	    每个聊天自动保存为 JSON 文件，可查看、加载、删除
✅ Markdown        渲染	AI 回复使用 Markdown 高亮展示，支持格式、代码块等
✅ API 接入	       接入 DeepSeek 官方 API, 可配置 API 密钥，支持保存
✅ 键盘快捷操作	    支持 Ctrl+N 新建、Ctrl+D 删除聊天等快捷方式
✅ 异步处理	       异步请求发送/接收，防止界面卡顿
"""

import os  # 导入操作系统相关模块
import json  # 导入 JSON 处理模块
from pathlib import Path  # 导入路径处理模块
from datetime import datetime  # 导入日期时间模块
from typing import List, Dict, Optional, Tuple  # 导入类型注解
import httpx  # 导入 HTTP 客户端库
from rich.console import Console  # 导入 Rich 控制台
from rich.panel import Panel  # 导入 Rich 面板
from rich.markdown import Markdown  # 导入 Rich Markdown 渲染
from rich.text import Text  # 导入 Rich 文本
from textual import work, on  # 导入 Textual 装饰器
from textual.app import App, ComposeResult  # 导入 Textual 应用基类和组合结果
from textual.containers import VerticalScroll, Horizontal, Container  # 导入容器控件
from textual.widgets import (  # 导入常用控件
    Button,
    Header,
    Footer,
    Input,
    Static,
    ListView,
    ListItem,
    Label,
    LoadingIndicator
)
from textual.reactive import reactive  # 导入响应式变量
from textual.message import Message  # 导入消息基类

# 配置常量
CONFIG_DIR = Path.home() / ".deepseek_terminal"  # 配置文件夹路径
CONFIG_FILE = CONFIG_DIR / "config.json"         # 配置文件路径
CHAT_HISTORY_DIR = CONFIG_DIR / "chats"          # 聊天记录文件夹
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek API 地址
DEFAULT_MODEL = "deepseek-chat"                  # 默认模型名称

# 确保配置目录存在
CONFIG_DIR.mkdir(parents=True, exist_ok=True)  # 创建配置目录（如不存在）
CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)  # 创建聊天历史目录

# 初始化控制台
console = Console()  # Rich 控制台对象

class DeepSeekClient:
    """
    DeepSeek API 客户端，负责与 DeepSeek 后端进行 HTTP 通信。
    """
    def __init__(self, api_key: str):
        self.api_key = api_key  # 保存 API 密钥
        self.base_url = DEEPSEEK_API_URL  # API 基础地址
        self.headers = {  # 请求头
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.model = DEFAULT_MODEL  # 默认模型
        
    def chat(self, messages: List[Dict[str, str]]) -> Tuple[Optional[str], Optional[str]]:
        """
        向 DeepSeek API 发送聊天消息，返回 AI 回复内容和错误信息。
        :param messages: 聊天消息历史，格式为 [{role:..., content:...}, ...]
        :return: (回复内容, 错误信息)
        """
        payload = {  # 构造请求体
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }
        try:
            response = httpx.post(  # 发送 POST 请求
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()  # 检查 HTTP 状态码
            data = response.json()  # 解析响应 JSON
            if "choices" in data and data["choices"]:  # 检查 choices 字段
                choice = data["choices"][0]  # 取第一个回复
                if "message" in choice and "content" in choice["message"]:  # 检查内容
                    return choice["message"]["content"], None  # 返回内容
            return None, "API响应中没有找到回复内容"  # 未找到内容
        except httpx.HTTPStatusError as e:
            return None, f"API错误: {e.response.status_code} - {e.response.text}"  # HTTP 错误
        except httpx.RequestError as e:
            return None, f"网络请求错误: {str(e)}"  # 网络错误
        except Exception as e:
            return None, f"未知错误: {str(e)}"  # 其他异常

class ChatHistory:
    """
    聊天历史管理类，负责聊天记录的创建、保存、加载、删除等操作。
    聊天记录以 JSON 文件形式存储在本地。
    """
    def __init__(self):
        self.storage_dir = CHAT_HISTORY_DIR  # 聊天记录目录
        self.storage_dir.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        self.current_chat_id = None  # 当前聊天 ID
        self.current_chat = []  # 当前聊天内容
        
    def new_chat(self) -> str:
        """创建新聊天并返回聊天ID(以时间戳命名)"""
        chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")  # 生成唯一聊天 ID
        self.current_chat_id = chat_id  # 设置当前聊天 ID
        self.current_chat = []  # 清空当前聊天内容
        return chat_id  # 返回新聊天 ID
        
    def save_chat(self):
        """保存当前聊天到文件（仅当有聊天内容时）"""
        if not self.current_chat_id or not self.current_chat:  # 没有内容不保存
            return
            
        chat_file = self.storage_dir / f"{self.current_chat_id}.json"  # 聊天文件路径
        with open(chat_file, "w", encoding="utf-8") as f:  # 打开文件写入
            json.dump({
                "id": self.current_chat_id,
                "messages": self.current_chat,
                "created": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def load_chat(self, chat_id: str) -> bool:
        """加载指定聊天ID的聊天内容到当前会话"""
        chat_file = self.storage_dir / f"{chat_id}.json"  # 聊天文件路径
        if chat_file.exists():  # 文件存在
            try:
                with open(chat_file, "r", encoding="utf-8") as f:  # 打开文件读取
                    data = json.load(f)  # 解析 JSON
                    self.current_chat_id = data["id"]  # 设置当前聊天 ID
                    self.current_chat = data["messages"]  # 设置当前聊天内容
                    return True  # 加载成功
            except:
                return False  # 加载失败
        return False  # 文件不存在
    
    def get_chat_list(self) -> List[Dict]:
        """
        获取所有聊天历史的简要信息列表（用于侧边栏展示）。
        每个聊天以第一条用户消息为标题。
        """
        chats = []  # 聊天列表
        for file in self.storage_dir.glob("*.json"):  # 遍历所有聊天文件
            try:
                with open(file, "r", encoding="utf-8") as f:  # 打开文件
                    data = json.load(f)  # 解析 JSON
                    
                    # 获取第一条用户消息作为标题
                    title = "新聊天"
                    for msg in data["messages"]:
                        if msg["role"] == "user":
                            title = msg["content"].strip()
                            if len(title) > 30:
                                title = title[:27] + "..."
                            break
                    
                    # 解析时间
                    created_time = datetime.fromisoformat(data.get("created", "2023-01-01T00:00:00"))
                    modified_time = datetime.fromisoformat(data.get("last_modified", "2023-01-01T00:00:00"))
                    
                    chats.append({
                        "id": data["id"],
                        "title": title,
                        "created": created_time.strftime("%Y-%m-%d %H:%M"),
                        "modified": modified_time.strftime("%Y-%m-%d %H:%M"),
                        "message_count": len(data["messages"])
                    })
            except:
                continue  # 解析失败跳过
        
        # 按修改时间倒序排列
        return sorted(chats, key=lambda x: x["modified"], reverse=True)
    
    def add_message(self, role: str, content: str):
        """向当前聊天添加一条消息，并自动保存"""
        self.current_chat.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save_chat()  # 自动保存
    
    def delete_chat(self, chat_id: str) -> bool:
        """删除指定聊天ID的聊天记录文件"""
        chat_file = self.storage_dir / f"{chat_id}.json"  # 聊天文件路径
        if chat_file.exists():  # 文件存在
            try:
                chat_file.unlink()  # 删除文件
                return True
            except:
                return False  # 删除失败
        return False  # 文件不存在

class ChatDisplay(Static):
    """
    聊天消息显示区域，负责将用户和 AI 消息以富文本面板形式展示。
    """
    def add_message(self, role: str, content: str):
        """添加一条消息到显示区域，区分用户和 AI 样式"""
        timestamp = datetime.now().strftime("%H:%M:%S")  # 当前时间
        
        if role == "user":  # 用户消息样式
            panel = Panel(
                content,
                title=f"You [{timestamp}]",
                title_align="right",
                style="bold blue",
                border_style="blue",
                width=80,
                padding=(0, 1, 1, 1)
            )
        else:  # AI 消息样式
            md = Markdown(content)  # 渲染为 Markdown
            panel = Panel(
                md,
                title=f"DeepSeek AI [{timestamp}]",
                style="bold green",
                border_style="green",
                width=80,
                padding=(0, 1, 1, 1)
            )
        
        self.mount(Static(panel))  # 将 Rich Panel 包装在 Static 组件中
        self.call_after_refresh(self.scroll_end)  # 滚动到底部
    
    def scroll_end(self):
        """滚动到底部，确保最新消息可见"""
        self.scroll_to(0, 10000, animate=False)
    
    def clear_chat(self):
        """清空聊天显示区域"""
        self.remove_children()

class ChatHistoryItem(ListItem):
    """
    聊天历史列表项，显示单个聊天的标题和时间等信息。
    """
    def __init__(self, chat: Dict):
        super().__init__()  # 调用父类构造
        self.chat_id = chat["id"]  # 聊天 ID
        self.chat_data = chat  # 聊天数据

    def compose(self) -> ComposeResult:
        # 使用 Compose API 挂载子组件
        title = Text(self.chat_data["title"], style="bold")  # 标题
        time_info = Text(f"{self.chat_data['created']} • {self.chat_data['message_count']}条消息", style="dim")  # 时间和消息数
        label = Text.assemble(title, "\n", time_info)  # 合并文本
        yield Label(label)  # 生成标签

class ChatHistoryList(ListView):
    """
    聊天历史列表控件，负责加载和展示所有历史聊天。
    通过消息机制通知主程序聊天被选中或删除。
    """
    class ChatSelected(Message):
        """当选择聊天时发送的消息"""
        def __init__(self, chat_id: str):
            super().__init__()
            self.chat_id = chat_id  # 聊天 ID
    
    class ChatDeleted(Message):
        """当删除聊天时发送的消息"""
        def __init__(self, chat_id: str):
            super().__init__()
            self.chat_id = chat_id  # 聊天 ID
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # 父类初始化
        self.chats = []  # 聊天列表
    
    def load_chats(self, chats: List[Dict]):
        """加载聊天历史列表到控件"""
        self.clear()  # 清空现有项
        self.chats = chats  # 保存聊天数据
        for chat in chats:
            self.append(ChatHistoryItem(chat))  # 添加每个聊天项
    
    async def on_list_view_selected(self, event: ListView.Selected):
        """当用户选择某个聊天历史项时触发，发送 ChatSelected 消息"""
        if isinstance(event.item, ChatHistoryItem):
            chat_id = event.item.chat_id  # 获取聊天 ID
            self.post_message(self.ChatSelected(chat_id))  # 发送消息

class StatusBar(Static):
    """
    状态栏组件，用于显示应用当前状态或提示信息。
    """
    status = reactive("就绪")  # 响应式状态文本
    
    def watch_status(self, status: str):
        self.update(Text(status, style="dim"))  # 更新状态栏内容

class DeepSeekApp(App):
    """
    DeepSeek AI 终端主应用类，负责界面布局、事件处理、与 API 交互、CSS主题、组件样式等
    """
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 3fr;
        grid-rows: 1fr auto;
        padding: 1;
    }
    
    #sidebar {
        width: 100%;
        height: 100%;
        border: solid $accent;
        background: $panel;
    }
    
    #chat-container {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    
    #input-container {
        width: 100%;
        height: auto;
        dock: bottom;
        margin-top: 1;
    }
    
    #chat-display {
        height: 1fr;
        overflow-y: auto;
        border: solid $accent;
        padding: 1;
        background: $surface;
    }
    
    #chat-input {
        width: 80%;
    }
    
    #send-button {
        width: 20%;
    }
    
    #status-bar {
        height: 1;
        dock: bottom;
        padding: 0 1;
    }
    
    #chat-list-container {
        height: 1fr;
    }
    
    #sidebar-buttons {
        height: auto;
        padding: 1;
        width: 100%;
        align: center middle;
    }
    
    #new-chat-button {
        width: 100%;
    }
    
    .error-panel {
        background: $error;
        color: white;
        padding: 1;
        border: round red;
    }
    
    .loading-container {
        align: center middle;
        height: 3;
    }
    """
    
    BINDINGS = [
        ("ctrl+n", "new_chat", "新建聊天"),
        ("ctrl+d", "delete_chat", "删除聊天"),
        ("ctrl+q", "quit", "退出"),
    ]
    
    def __init__(self, api_key: str):
        super().__init__()  # 父类初始化
        self.client = DeepSeekClient(api_key)  # DeepSeek API 客户端
        self.history = ChatHistory()           # 聊天历史管理
        self.current_chat_id = None            # 当前聊天ID
    
    def compose(self) -> ComposeResult:
        """
        组合应用界面，定义侧边栏、主聊天区、输入区、状态栏等。
        """
        yield Header(show_clock=True)  # 顶部标题栏
        
        # 侧边栏
        with Container(id="sidebar"):
            with Container(id="sidebar-buttons"):
                yield Button("新建聊天", id="new-chat", variant="primary")  # 新建聊天按钮
            yield VerticalScroll(id="chat-list-container")  # 聊天历史列表
        
        # 主聊天区
        with Container(id="chat-container"):
            yield ChatDisplay(id="chat-display")  # 聊天消息显示区
            with Horizontal(id="input-container"):
                yield Input(placeholder="输入消息...", id="chat-input")  # 输入框
                yield Button("发送", id="send-button", variant="success")  # 发送按钮

        yield StatusBar(id="status-bar")  # 状态栏
        yield Footer()  # 底部栏
    
    def on_mount(self) -> None:
        """
        应用挂载时初始化，加载聊天历史并创建新聊天。
        """
        self.title = "DeepSeek AI 终端"  # 应用标题
        self.sub_title = "与 DeepSeek AI 聊天"  # 子标题
        self.query_one("#status-bar").status = "就绪 | 按 Ctrl+N 新建聊天，Ctrl+D 删除当前聊天"
        
        # 加载聊天历史列表
        self.load_chat_history()
        
        # 创建新聊天
        self.create_new_chat()
        
        # 设置焦点到输入框
        self.query_one("#chat-input").focus()
    
    def load_chat_history(self):
        """
        加载聊天历史到侧边栏列表。
        """
        chats = self.history.get_chat_list()  # 获取聊天列表
        chat_list_container = self.query_one("#chat-list-container")  # 获取容器
        chat_list_container.remove_children()  # 先清除现有内容
        
        # 创建并加载聊天列表
        chat_list = ChatHistoryList()  # 聊天历史控件
        chat_list_container.mount(chat_list)  # 挂载到容器
        chat_list.load_chats(chats)  # 加载聊天项

    
    def create_new_chat(self):
        """
        创建新聊天会话并清空聊天显示区。
        """
        self.current_chat_id = self.history.new_chat()  # 新建聊天
        self.query_one("#chat-display").clear_chat()  # 清空显示区
        self.query_one("#chat-input").focus()  # 聚焦输入框
        self.query_one("#status-bar").status = f"新聊天会话已创建: {self.current_chat_id}"
    
    def add_message_to_chat(self, role: str, content: str):
        """
        向当前聊天添加消息，并同步到显示区。
        """
        self.history.add_message(role, content)  # 添加到历史
        self.query_one("#chat-display").add_message(role, content)  # 添加到显示区
        self.query_one("#status-bar").status = f"消息已添加 | 当前聊天: {self.current_chat_id}"
    
    def show_error(self, message: str):
        """
        在状态栏和聊天区显示错误信息。
        """
        self.query_one("#status-bar").status = f"错误: {message}"  # 状态栏显示
        error_panel = Panel(message, title="错误", style="red")  # 创建错误面板
        self.query_one("#chat-display").mount(Static(error_panel))  # 聊天区显示
    
    def show_loading(self, show: bool):
        """
        控制输入区的加载指示器显示/隐藏。
        """
        input_container = self.query_one("#input-container")  # 输入区容器
        loading_containers = input_container.query("#loading-container")  # 查找加载指示器
    
        if show:
            if not loading_containers:  # 没有则添加
                container = Container(id="loading-container", classes="loading-container")
                input_container.mount(container)
                loading_indicator = LoadingIndicator(id="loading-indicator")
                container.mount(loading_indicator)
        else:
            for container in loading_containers:  # 有则移除
                container.remove()
    
    @work(exclusive=True)
    async def send_message(self, message: str):
        """
        发送消息到 DeepSeek API，处理响应并更新界面。
        """
        if not message.strip():  # 空消息不处理
            return
            
        # 添加用户消息
        self.add_message_to_chat("user", message)
        
        # 显示加载指示器
        self.show_loading(True)
        self.query_one("#send-button").disabled = True
        self.query_one("#chat-input").disabled = True
        
        try:
            # 调用 API
            content, error = self.client.chat(self.history.current_chat)
            
            if error:
                self.show_error(error)
            elif content:
                # 添加 AI 响应
                self.add_message_to_chat("assistant", content)
            else:
                self.show_error("未收到有效响应")
                
        except Exception as e:
            self.show_error(f"请求失败: {str(e)}")
        finally:
            # 隐藏加载指示器
            self.show_loading(False)
            self.query_one("#send-button").disabled = False
            self.query_one("#chat-input").disabled = False
            self.query_one("#chat-input").focus()
    
    def confirm_dialog(self, message: str) -> bool:
        """
        简易确认对话框（终端输入版）。
        """
        self.query_one("#status-bar").status = f"{message} [按 Y 确认，其他键取消]"
        return input(f"{message} [y/N] ").strip().lower() == 'y'  # 终端输入
    
    def action_new_chat(self):
        """
        新建聊天快捷键操作。
        """
        self.create_new_chat()
    
    def action_delete_chat(self):
        """
        删除当前聊天快捷键操作。
        """
        if self.current_chat_id:
            if self.confirm_dialog(f"确定要删除当前聊天 '{self.current_chat_id}' 吗?"):
                if self.history.delete_chat(self.current_chat_id):
                    self.query_one("#status-bar").status = f"聊天 '{self.current_chat_id}' 已删除"
                    self.create_new_chat()
                    self.load_chat_history()
                else:
                    self.show_error("删除聊天失败")

    @on(Button.Pressed, "#new-chat")
    def on_new_chat(self):
        """
        新建聊天按钮点击事件。
        """
        self.action_new_chat()
    
    @on(Button.Pressed, "#send-button")
    def on_send_button(self):
        """
        发送按钮点击事件。
        """
        input_widget = self.query_one("#chat-input")  # 获取输入框
        message = input_widget.value.strip()  # 获取输入内容
        if message:
            self.send_message(message)  # 发送消息
            input_widget.value = ""  # 清空输入框
    
    @on(Input.Submitted, "#chat-input")
    def on_input_submitted(self, event: Input.Submitted):
        """
        输入框回车提交事件。
        """
        if event.value.strip():
            self.send_message(event.value)  # 发送消息
            event.input.value = ""  # 清空输入框
    
    @on(ChatHistoryList.ChatSelected)
    def on_chat_selected(self, event: ChatHistoryList.ChatSelected):
        """
        聊天历史项被选中时加载对应聊天内容。
        """
        if self.history.load_chat(event.chat_id):
            self.current_chat_id = event.chat_id  # 设置当前聊天 ID
            chat_display = self.query_one("#chat-display")  # 获取显示区
            chat_display.clear_chat()  # 清空显示区
            for msg in self.history.current_chat:  # 加载历史消息
                chat_display.add_message(msg["role"], msg["content"])
            self.query_one("#chat-input").focus()  # 聚焦输入框
            self.query_one("#status-bar").status = f"已加载聊天: {self.current_chat_id}"
    
    @on(ChatHistoryList.ChatDeleted)
    def on_chat_deleted(self, event: ChatHistoryList.ChatDeleted):
        """
        聊天历史项被删除时的处理。
        """
        if self.history.delete_chat(event.chat_id):
            self.query_one("#status-bar").status = f"聊天 '{event.chat_id}' 已删除"
            if self.current_chat_id == event.chat_id:  # 删除的是当前聊天
                self.create_new_chat()
            self.load_chat_history()  # 刷新聊天列表

def load_api_key() -> Optional[str]:
    """
    加载 API 密钥，优先从环境变量读取，否则从配置文件读取。
    """
    key = os.getenv("DEEPSEEK_API_KEY")  # 先查环境变量
    if key:
        return key

    if CONFIG_FILE.exists():  # 配置文件存在
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("api_key")
        except json.JSONDecodeError:
            console.print("[bold red]警告: 配置文件格式错误，无法读取 API 密钥[/bold red]")
    return None

def save_api_key(api_key: str):
    """
    保存 API 密钥到本地配置文件。
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)  # 确保目录存在
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"api_key": api_key}, f, ensure_ascii=False, indent=2)

def main():
    """
    应用程序入口，负责密钥校验、应用启动等。
    """
    api_key = load_api_key()  # 加载密钥
    if not api_key:
        console.print("\n[bold yellow]第一次使用 DeepSeek 终端工具[/bold yellow]")
        console.print("请从 DeepSeek 官网获取 API 密钥: https://platform.deepseek.com/api-keys")
        api_key = input("请输入您的 DeepSeek API 密钥: ").strip()
        if not api_key:
            console.print("[bold red]错误: 必须提供 API 密钥[/bold red]")
            exit(1)
        save_api_key(api_key)
        console.print("[green]API 密钥已保存至配置文件[/green]"),

    if not api_key.startswith("sk-"):  # 校验密钥格式
        console.print(f"[bold red]错误: 无效的 API 密钥格式[/bold red] 键应以 'sk-' 开头，您提供: {api_key[:6]}...{api_key[-6:]}")
        exit(1)

    try:
        app = DeepSeekApp(api_key)  # 创建应用
        app.run()  # 运行应用
    except Exception as e:
        console.print(f"[bold red]启动应用程序时出错:[/bold red] {e}")
        exit(1)

if __name__ == "__main__":
    main()  # 程序入口