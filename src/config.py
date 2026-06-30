from pathlib import Path
import fileUtils
import models
import tools

DEFAULT_SETTING_YAML = """\
#这是介绍页生成的选项
homePage:  
  enable: true
  #可选的参数有 {bookID} {bookCover} {bookName} {bookAuthor} {bookDescription} {Enter}
  style: "{bookCover}{Enter}书名:{bookName}{Enter}作者:{bookAuthor}{Enter}描述:{bookDescription}"

#这是批量模式的开启选项
batch:
  enable: false
  #打开这个选项能让程序自动处理目录下的以数字为名的文件夹，而queue中的内容会被忽略
  auto: true
  #单书模式时直接指定url或id，留空则在交互模式下询问
  url: ""
  #输入你想处理的书籍的url或者id
  queue:
    - 100000000
    - 200000000

#这是缓存的选项
cache:
  #生成文本的缓存
  text: true
  #可选的参数有 {bookID} {bookCover} {bookName} {bookAuthor} {bookDescription}
  textFolder: "data/decrypted/{bookID}/text"
  #生成图片的缓存
  image: true
  #可选的参数有 {bookID} {bookCover} {bookName} {bookAuthor} {bookDescription}
  imageFolder: "data/decrypted/{bookID}/images"

#日志相关的设置
log:
  #关闭这个选项会忽略"xxx章未购买"的警告
  notFoundWarn: true

#多线程相关的设置
multiThread:
  #最大线程数
  maxWorkers: 8

#adb自动拉取的设置选项
adb:
  enable: true
  #留空则自动检测，多设备时自动选择安装了刺猬猫的设备
  device: ""
  #打开这个选项能让程序自动扫描设备上的所有书籍，此时books设置会被忽略
  auto: true
  #当auto为false时，手动指定需要拉取的book_id列表
  books:
    - 100000000

#交互模式的设置选项
interactive:
  #auto = 配置文件完整时无交互运行，不完整时弹出菜单
  #always = 始终显示菜单
  #never = 绝不显示菜单，配置不完整时报错退出
  mode: auto
"""
setting = None
textFolder = ""
imageFolder = ""

def init():
    global setting
    config_path = Path("setting.yaml")
    if not config_path.exists():
        models.Print.warn(f"[WARN] 找不到 setting.yaml，使用默认配置继续...")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_SETTING_YAML)

    try:
        setting = fileUtils.loadSetting(config_path)
    except Exception as e:
        models.Print.err(f"[ERR] {e}")
        return
    global textFolder
    global imageFolder
    textFolder = ""
    imageFolder = ""
    return

def CalculateParama(book:models.Book):
    book.safeName = tools.SanitizeName(book.name)
    book.decryptedTxt = Path("output") / f"{book.safeName}.txt"
    count = 0
    for division in book.divisions:
        for chapter in division.chapters:
            count += 1
            chapter.safeTitle = tools.SanitizeName(chapter.title)
            if setting.cache.text:
                chapter.decrypted = Path(textFolder) / f"{count} {chapter.safeTitle}.txt"
            chapter.key = Path("data/key") / str(chapter.id)
            chapter.encryptedTxt = Path("data") / str(book.id) / f"{chapter.id}.txt"
    return