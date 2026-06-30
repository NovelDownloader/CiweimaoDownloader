from colorama import init, Fore, Style, Back
from pydantic import BaseModel
from dataclasses import dataclass,field
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Literal
from pathlib import Path
import requests

# 类型
@dataclass
class Chapters:
    id: int = field(default_factory=int)
    decrypted: Path = field(default_factory=Path)
    key: Path = field(default_factory=Path)
    encryptedTxt: Path = field(default_factory=Path)
    title: str = field(default_factory=str)
    safeTitle: str = field(default_factory=str)
    content:str = field(default_factory=str)
    auth_access:bool = field(default_factory=bool)
    isDownload: bool = field(default_factory=bool)

@dataclass
class Division:
    id: int = field(default_factory=int)
    title: str = field(default_factory=str)
    maxChapterIndex: int = field(default_factory=int)
    chapters:list = field(default_factory=list)

@dataclass
class Book:
    id: int = field(default_factory=int)
    url: str = field(default_factory=str)
    divisions: list = field(default_factory=list)
    safeName: str = "未命名"
    name: str = "未命名"
    author: str = "佚名"
    cover: Optional[bytes] = field(default_factory=bytes)
    coverUrl: str = field(default_factory=str)
    description: str = field(default_factory=str)
    
    # decryptedFolder: Path = field(default_factory=Path)
    decryptedTxt: Path = field(default_factory=Path)

# 日志输出设置
init(autoreset=True)
class Print:
    @staticmethod
    def err(msg): print(Back.RED + Fore.WHITE + Style.BRIGHT + f"{msg}")
    @staticmethod
    def warn(msg): print(Back.LIGHTYELLOW_EX + Fore.BLACK + Style.BRIGHT + f"{msg}")
    @staticmethod
    def info(msg): print(f"{msg}")
    @staticmethod
    def processingLabel(msg):
        return Back.LIGHTBLUE_EX + Style.BRIGHT + Fore.WHITE + f"{msg}" + Style.RESET_ALL

# 网络出错重试
class Requests:
    def __init__(self, maxRetries=3, backoff=0.5, timeout=10):
        self.maxRetries = maxRetries
        self.backoff = backoff
        self.timeout = timeout
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6788.76 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }

        retry_strategy = Retry(
            total=self.maxRetries,
            status_forcelist=[403, 404, 429, 500, 502, 503, 504],
            allowed_methods={"GET", "POST"},
            backoff_factor=self.backoff
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _request(self, method, url, **kwargs):
        try:
            return self.session.request(method, url, timeout=self.timeout, **kwargs)

        except RuntimeError:
            # 只要 session 被关闭，必然是 RuntimeError
            self._init_session()
            return self.session.request(method, url, timeout=self.timeout, **kwargs)

    def get(self, url, params=None):
        return self._request("GET", url, params=params or {})

    def post(self, url, data=None):
        return self._request("POST", url, data=data or {})
    
# yaml配置文件
class homePageConfig(BaseModel):
    enable: bool = False
    style: str = "<bookCover>\n书名:<bookName>\n作者:<bookAuthor>\n描述:<bookDescription>"

class cacheConfig(BaseModel):
    text: bool = True
    textFolder: str = "decrypted/{bookID}/text"
    image: bool = False
    imageFolder: str = "decrypted/{bookID}/images"

class logConfig(BaseModel):
    notDownloadWarn : bool =  True
    notAuthWarn : bool =True

class multiThreadConfig(BaseModel):
    maxWorkers: int = 8

class adbConfig(BaseModel):
    enable: bool = False
    device: str = ""

class Config(BaseModel):
    homePage: homePageConfig
    cache: cacheConfig
    log: logConfig
    multiThread: multiThreadConfig
    adb: adbConfig
