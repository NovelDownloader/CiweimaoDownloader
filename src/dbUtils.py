from inspect import Parameter
import sqlite3
import models
import json

class DBHelper:
	def __init__(self, db_path: str):
		self.db_path = db_path
		self.conn = sqlite3.connect(db_path)
		self.conn.row_factory = sqlite3.Row   # 可选，便于按列名访问

	def get_book_info(self, book_id: int) -> dict:
		# cursor.execute("SELECT book_info FROM shelf_book_info WHERE book_id = ?", (book_id,))
		result = self.execute_query("SELECT book_info FROM shelf_book_info WHERE book_id = ?", (book_id,))
		if result:
			return json.loads(result[0][0])
		return dict()

	def get_divisions(self, book_id: int) -> list:
		sql = """
			SELECT division_id, division_index, max_chapter_index, division_name
			FROM division
			WHERE book_id = ?
		"""
		rows = self.execute_query(sql, (book_id,))

		# 按 division_index 排序（元组索引 1）
		sorted_rows = sorted(rows, key=lambda row: row[1])

		# 构建
		result = list()
		for division_id, division_index, max_chapter_index, division_name in sorted_rows:
			division = models.Division()
			division.id = division_id
			division.title = division_name
			division.maxChapterIndex = max_chapter_index
			result.append(division)
		return result


	def get_chapters(self, book_id: int, division_id: int) -> list:
		"""
		根据 book_id 和 division_id 获取所有章节信息，
		按 chapter_id 升序排序后返回有序字典。

		参数:
			book_id (int): 书籍 ID
			division_id (int): 分卷 ID

		返回:
			dict: 键为 chapter_id，值为包含 chapter_title、
						 chapter_index、auth_access、is_download 的字典
		"""
		sql = """
			SELECT chapter_id, chapter_title, chapter_index, auth_access, is_download
			FROM catalog1
			WHERE book_id = ? AND division_id = ?
		"""
		rows = self.execute_query(sql, (book_id, division_id))

		# 按 chapter_id 排序（元组索引 2）
		sorted_rows = sorted(rows, key=lambda row: row[2])

		# 构建
		result = list()
		for chapter_id, chap_title, chap_index, auth_access, is_download in sorted_rows:
			chapter = models.Chapters()
			chapter.id = chapter_id
			chapter.title = chap_title
			chapter.auth_access = auth_access
			chapter.isDownload = is_download
			result.append(chapter)
		return result	
 
	def execute_query(self, sql:str, params=()):
		cursor = self.conn.cursor()
		cursor.execute(sql, params)
		return cursor.fetchall()

	def close(self):
		self.conn.close()
