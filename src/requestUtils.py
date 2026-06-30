import models
import requests
from bs4 import BeautifulSoup

def GetDescription(book_id) -> str: #方法，获取书籍信息
    url = f"https://www.ciweimao.com/book/{book_id}"

    try:
        try:
            response = models.Requests().post(url)
        except Exception as e:
            models.Print.warn(f"[WARN] {e}")
            return ""
    
        soup = BeautifulSoup(response.text, "html.parser")

        description_tag = soup.find("meta", property="og:description")

        if not (description_tag):
            raise ValueError(f"[WARN] 缺失必要的 meta 标签")

        description = description_tag["content"]

        return str(description)

    except Exception as e:
        models.Print.warn(f"[WARN] 网络获取书籍描述失败: {e}")
        return ""

def GetCover(cover_url) -> bytes: #方法，获取书籍信息
    
    try:
        try:
            CoverResponse = models.Requests().get(cover_url)
        except requests.RequestException:
            return bytes()
    
        return CoverResponse.content
    except Exception as e:
        models.Print.warn(f"[WARN] 封面图片获取失败: {e}")
        return bytes()
