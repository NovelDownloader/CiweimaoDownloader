# =============================== #
#   EPUB Pipeline Generator       #
#   Threaded Producer + Async Consumer
#   Designed for high performance &
#   low memory usage EPUB building
# =============================== #

import models
import uuid
import tools
import asyncio
import json
import re
import aiofiles
import config
from ebooklib import epub
from asyncHttp import AsyncHTTP
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from tqdm import tqdm

# ---------------------------------------
# STEP 1: ========== 章解析（同步多线程）
# ---------------------------------------

def parse_chapter(idx: int, chapter: models.Chapters):
    """解析章节，不下载图片，只抽取 URL + 生成 HTML."""
    try:
        raw = chapter.content or ""
        
        pattern = r'<Book\s*(\{.*?\})\s*>'

        def replace_book_tag(match: re.Match) -> str:
            data = json.loads(match.group(1))
            return f'此为作者推书，书名：{data.get("book_name","")}，ID：{data.get("book_id","")}'

        result = re.sub(pattern, replace_book_tag, raw)
        
        soup = BeautifulSoup(result, "html.parser")

        # 删除 span
        for span in soup.find_all('span'):
            span.decompose()

        img_urls = []
        for img in soup.find_all('img'):
            src = img.get("src")
            if not src:
                img.decompose()
                continue

            parsed = urlparse(str(src))
            if parsed.scheme in ("http", "https"):
                img_urls.append(str(src))
            else:
                img.decompose()

        text = str(soup)
        paragraphs = re.split(r'(?=　　)', text)
        html = ''.join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

        return idx, chapter.title ,html, img_urls, None
    except Exception as e:
        return idx, None, None, [], e


# ---------------------------------------
# STEP 2: ========== Pipeline: 图片下载器
# ---------------------------------------

async def fetch_with_cache(url: str) -> tuple[str, bytes | None]:
    """下载单图，支持缓存，失败返回 None."""

    parsed = urlparse(url)
    fname = parsed.path.split("/")[-1] or uuid.uuid4().hex
    cache_path = Path(config.imageFolder) / fname

    # 如果开启缓存 & 存在
    if (
        getattr(config, "setting", None)
        and getattr(config.setting, "cache", None)
        and getattr(config.setting.cache, "image", False)
        and cache_path.exists()
    ):
        try:
            async with aiofiles.open(cache_path, "rb") as f:
                return url, await f.read()
        except:
            pass  # 缓存读取失败则继续下载

    # 网络下载
    try:
        data = await AsyncHTTP.get(url)
    except Exception as e:
        models.Print.err(f"[ERR] 下载失败: {url} {e}")
        return url, None

    # 写缓存
    if (
        getattr(config, "setting", None)
        and getattr(config.setting, "cache", None)
        and getattr(config.setting.cache, "image", False)
    ):
        try:
            Path(config.imageFolder).mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(cache_path, "wb") as f:
                await f.write(data)
        except:
            pass

    return url, data


async def image_worker(queue: asyncio.Queue,
                       results: dict[str, bytes | None],
                       sem: asyncio.Semaphore,
                       pbar: tqdm):
    """消费者 worker：持续从队列取 URL，下载，保存结果."""
    while True:
        url = await queue.get()
        if url is None:       # poison pill
            queue.task_done()
            return

        async with sem:
            u, data = await fetch_with_cache(url)
            results[u] = data

        pbar.update(1)
        
        queue.task_done()


# ---------------------------------------
# STEP 3: ========== 主流程
# ---------------------------------------

def GenerateEpub(book: models.Book,
                 output_path: str,
                 max_workers: int = 8,
                 max_img_tasks: int = 16):

    # 初始化 EPUB
    epub_book = epub.EpubBook()
    epub_book.set_title(book.name)
    epub_book.add_author(book.author)
    epub_book.set_language("zh")

    # 封面
    try:
        mime, ext = tools.CheckImageMIME(book.cover)
        if ext.startswith("."):
            ext = ext[1:]
        epub_book.set_cover(f"cover.{ext}", book.cover)
    except Exception as e:
        models.Print.warn(f"[WARN] 封面读取失败: {e}")

    # ===============================
    # A. 多线程解析章节（生产者）
    # ===============================
    chapter_infos = []
    all_urls = []

    tasks = []
    idx = 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {}

        for division in book.divisions:
            for chap in division.chapters:
                futures[pool.submit(parse_chapter, idx, chap)] = (
                    idx,
                    division,
                    chap
                )
                idx += 1

        for fut in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="[PROCESS] 解析章节..."
        ):
            idx, division, chap = futures[fut]

            _, title, html, urls, err = fut.result()

            if err:
                ...
                continue

            chapter_infos.append(
                (idx, division, chap, title, html)
            )

            all_urls.extend(urls)
    chapter_infos.sort(key=lambda x: x[0])

    # ===============================
    # B. 异步图片下载 Pipeline
    # ===============================

    async def pipeline_main(unique_urls: list[str], pbar: tqdm):
        """一个事件循环，生产者（线程池部份）已把 URL 提供给我们。"""
        await AsyncHTTP.init()             # 启动 HTTP session

        queue = asyncio.Queue()
        results = {}                        # url → bytes

        # 去重后的 URL 塞入队列（producer）
        for u in unique_urls:
            queue.put_nowait(u)

        # 控制并发
        sem = asyncio.Semaphore(max_img_tasks)

        # 启动 workers
        workers = [
            asyncio.create_task(image_worker(queue, results, sem, pbar))
            for _ in range(max_img_tasks)
        ]

        # 塞入 poison pill
        for _ in workers:
            queue.put_nowait(None)

        await queue.join()

        # 停掉 workers
        for w in workers:
            w.cancel()

        try:
            await AsyncHTTP.close()
        except:
            pass

        return results
    
    unique_urls = list(dict.fromkeys(all_urls))
    if unique_urls:
        pbar = tqdm(total=len(unique_urls), desc=models.Print.processingLabel(f"[PROCESSING] 正在下载图片"))
        url_to_bytes = asyncio.run(pipeline_main(unique_urls, pbar))
    else:
        url_to_bytes = {}

    # ===============================
    # C. 添加图片到 EPUB + 替换 HTML src
    # ===============================
    url_to_epubpath = {}

    for url, data in url_to_bytes.items():
        if not data:
            continue

        mime, ext = tools.CheckImageMIME(data)
        if ext.startswith("."):
            ext = ext[1:]
        filename = f"{uuid.uuid4().hex}.{ext}"
        epub_path = f"images/{filename}"

        item = epub.EpubItem(
            uid=f"img_{uuid.uuid4().hex}",
            file_name=epub_path,
            media_type=mime,
            content=data
        )
        epub_book.add_item(item)
        url_to_epubpath[url] = epub_path

    # ===============================
    # D. 构建章节
    # ===============================
    epub_chapters = []

    for idx, division, chapter, title, html in chapter_infos:
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all('img'):
            src = str(img.get("src", ""))
            if src in url_to_epubpath:
                img["src"] = url_to_epubpath[src]
            else:
                img.decompose()

        chap = epub.EpubHtml(
            title=title,
            file_name=f"chap_{idx + 1}.xhtml",
            lang="zh"
        )

        chap.content = f"<h1>{title}</h1>{soup}"
        epub_book.add_item(chap)

        epub_chapters.append(
            (
                idx,
                division,
                chap
            )
        )

    # ===============================
    # E. 目录 (TOC)
    # ===============================
    toc = []

    division_map = {}

    for idx, division, chap in epub_chapters:
        division_map.setdefault(
            division.id,
            {
                "title": division.title,
                "chapters": []
            }
        )

        division_map[division.id]["chapters"].append(chap)

    for div in book.divisions:

        info = division_map.get(div.id)

        if info is None:
            continue

        toc.append(
            (
                epub.Section(div.title),
                info["chapters"]
            )
        )

    # ===============================
    # F. 设置 spine & TOC
    # ===============================
    epub_book.set_identifier(str(uuid.uuid4()))
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())
    epub_book.spine = ['nav'] + [chap for _, _, chap in epub_chapters]
    epub_book.toc = toc

    # ===============================
    # G. 写入 EPUB
    # ===============================
    try:
        epub.write_epub(output_path, epub_book, {})
        models.Print.info(f"[INFO] EPUB 生成成功：{output_path}")
    except Exception as e:
        models.Print.err(f"[ERR] EPUB 写入失败: {e}")
