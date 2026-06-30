from urllib.parse import urlparse
from pathlib import Path
from tqdm import tqdm
import json

import models
import requestUtils
import dbUtils
import fileUtils
import epubUtils
import config
import tools
import decrypt

def adb_resolve_queue():
    """Build queue from config. Returns None if config is incomplete."""
    import adbUtils
    ids = adbUtils.list_books()
    if not ids:
        return None
    return ids


def process_book(entry: str):
    s = config.setting
    book = models.Book()

    book.url = entry
    try:
        book.id = int(urlparse(str(book.url)).path.split('/')[-1])
    except (ValueError, IndexError):
        try:
            book.id = int(str(entry).strip())
        except ValueError:
            models.Print.err(f"[ERR] 无效的书籍标识：{entry}")
            return

    if not isinstance(book.id, int):
        models.Print.err(f"[ERR] 错误的书籍标识：{entry}，这一项会被忽略")
        return

    # --- ADB pull ---
    if s.adb.enable:
        import adbUtils
        try:
            adbUtils.pull_book(book.id)
        except RuntimeError as e:
            models.Print.err(f"[ERR] ADB 拉取 {book.id} 失败：{e}")
            return

    # --- Preprocess ---
    fileUtils.RemoveNewlinesInEachFile(Path("data") / str(book.id))

    db = dbUtils.DBHelper("data/novelCiwei.db")
    book_info = db.get_book_info(book.id)
    book.name = book_info.get("book_name", "未命名")
    book.author = book_info.get("author_name", "未知作者")
    book.coverUrl = book_info.get("cover","")
    book.cover = requestUtils.GetCover(book.coverUrl)
    book.description = requestUtils.GetDescription(book.id)
    
    book.divisions = db.get_divisions(book.id)
    for devision in book.divisions:
        devision.chapters = db.get_chapters(book.id, devision.id)
    db.close()

    # --- Set up cache folders ---
    if s.cache.text:
        try:
            config.textFolder = tools.ProcessString(s.cache.textFolder, book)
            Path(config.textFolder).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            models.Print.err(f"[ERR] textFolder 无效：{e}")

    if s.cache.image:
        try:
            config.imageFolder = tools.ProcessString(s.cache.imageFolder, book)
            Path(config.imageFolder).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            models.Print.err(f"[ERR] imageFolder 无效：{e}")

    # --- Calculate derived paths ---
    config.CalculateParama(book)

    if book.decryptedTxt.exists():
        book.decryptedTxt.unlink(missing_ok=True)

    Path("output").mkdir(parents=True, exist_ok=True)

    # --- Decrypt chapters ---
    for devision in tqdm(book.divisions, desc=models.Print.processingLabel("[PROCESSING] 解码中")):
        for chapter in devision.chapters:
            # 读取缓存
            if chapter.decrypted.exists():
                try:
                    with open(chapter.decrypted, "r", encoding="utf-8") as f:
                        txt = f.read()
                    chapter.content = txt
                    with open(book.decryptedTxt, "a", encoding="utf-8") as f:
                        f.write(chapter.title + "\n" + txt + "\n\n")
                except Exception as e:
                    models.Print.err(f"[ERR] 读取缓存 {chapter.decrypted} 失败：{e}")
                continue

            if chapter.auth_access == False:
                if s.log.notAuthWarn:
                    models.Print.warn(f"[WARN] {chapter.title} 未购买")
                chapter.content = "未购买本章"
                continue

            if chapter.isDownload == False:
                if s.log.notDownloadWarn:
                    models.Print.warn(f"[WARN] {chapter.title} 未下载，请重新下载")
                chapter.content = "未下载本章，请重新下载"
                continue

            #解码
            try:
                with open(chapter.key, 'r', encoding="utf-8") as f:
                    seed = f.read()
                with open(chapter.encryptedTxt, 'r', encoding="utf-8") as f:
                    encryptedTxt = f.read()
                try:
                    txt = decrypt.decrypt(encryptedTxt, seed)
                    chapter.content = txt
                    if s.cache.text:
                        with open(chapter.decrypted, "w", encoding="utf-8") as f:
                            f.write(txt)
                    with open(book.decryptedTxt, "a", encoding="utf-8") as f:
                        f.write(f"{chapter.title}\n{txt}\n")
                except Exception as e:
                    models.Print.err(f"[ERR] 解密 {chapter.encryptedTxt} 失败：{e}")
                    continue
            except FileNotFoundError:
                if s.log.notDownloadWarn:
                    models.Print.warn(f"[WARN] 找不到 {chapter.title} ")
                chapter.content = "找不到本章，未知错误"
            except Exception as e:
                models.Print.warn(f"[WARN] {e}")

    models.Print.info(f"[INFO] txt文件已生成：{book.safeName}")
    models.Print.info(f"[INFO] 正在打包Epub...")

    if s.homePage.enable:
        models.Print.warn("[INFO] 检测到书籍主页选项打开")
        hp = models.Chapters(id=0, title=book.name)
        hp.content = tools.ProcessString(s.homePage.style, book)
        division = models.Division(title="首页")
        division.chapters.append(hp)
        book.divisions.insert(0, division)

    epubUtils.GenerateEpub(book, str(Path("output") / f"{book.safeName}.epub"))


def main():
    models.Print.info(
        "[INFO] 本程序基于Zn90107UlKa/CiweimaoDownloader@github.com\n"
        "[INFO] 如果您是通过被售卖的渠道获得的本软件，请您立刻申请退款。\n"
        "[INFO] 仅供个人学习与技术研究\n"
        "[INFO] 禁止任何形式的商业用途\n"
        "[INFO] 所有内容版权归原作者及刺猬猫平台所有\n"
        "[INFO] 请在 24 小时内学习后立即删除文件\n"
        "[INFO] 作者不承担因不当使用导致的损失及法律后果"
    )
    
    config.init()
    
    isPreQueued = False

    # ADB init
    if config.setting.adb.enable:
        import adbUtils
        try:
            adbUtils.check_adb()
            adbUtils.pull_keys()
            adbUtils.pull_db()
            
            preQueue = adb_resolve_queue()
            isPreQueued = True
        except RuntimeError as e:
            models.Print.err(f"[ERR] ADB 初始化失败：{e}")
    
    if isPreQueued == False:
        #Legacy-update
        preQueue = list()
        
        models.Print.info("[INFO] 现在进入传统模式")
        try:
            for folder in Path(".").iterdir():
                if folder.is_dir() and folder.name.isdigit():
                    preQueue.append(folder.name)
        except Exception as e:
            models.Print.err(f"[ERR] 自动寻找目录失败，原因是： {e}")
            return
    
    fileUtils.TransformFilename("data/key")
    
    # 打印书籍列表表格
    header = f"{'ID':<15}{'书名'}"
    separator = "-" * 40
    table_lines = [header, separator]
    for id in preQueue:
        db = dbUtils.DBHelper("data/novelCiwei.db")
        book_info = db.get_book_info(id)
        book_name = book_info.get("book_name", "未命名")
        table_lines.append(f"{str(id):<15}{book_name}")
    models.Print.info("\n".join(table_lines))

    models.Print.warn("[OPT] 请输入需要解码的书籍 ID（多个 ID 请用空格分隔）：")
    queueString = input()
    queue = queueString.split()  # 转换为列表
    
    if queue is None:
        return

    for entry in queue:
        try:
            process_book(entry)
        except Exception as e:
            models.Print.err(f"[ERR] 处理 {entry} 时发生未预期错误：{e}")


if __name__ == "__main__":
    main()
