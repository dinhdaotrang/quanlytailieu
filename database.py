"""
Module quản lý database để lưu trữ file và metadata
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json


class DocumentDB:
    """Class quản lý database cho tài liệu"""
    
    def __init__(self, db_path: str = "documents.db"):
        """
        Khởi tạo database
        
        Args:
            db_path: Đường dẫn đến file database
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Tạo connection đến database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Để trả về dict-like rows
        return conn
    
    def init_database(self):
        """Khởi tạo bảng trong database nếu chưa tồn tại"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Bảng documents: lưu thông tin file và nội dung
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_data BLOB NOT NULL,
                category TEXT NOT NULL,
                document_type TEXT,
                issuing_agency TEXT,
                issue_date DATE,
                content_text TEXT,
                classification_result TEXT,
                analysis_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Kiểm tra và thêm các cột mới nếu chưa tồn tại (migration)
        try:
            cursor.execute("PRAGMA table_info(documents)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'document_type' not in columns:
                cursor.execute("ALTER TABLE documents ADD COLUMN document_type TEXT")
            if 'issuing_agency' not in columns:
                cursor.execute("ALTER TABLE documents ADD COLUMN issuing_agency TEXT")
            if 'issue_date' not in columns:
                cursor.execute("ALTER TABLE documents ADD COLUMN issue_date DATE")
        except:
            pass  # Bỏ qua nếu có lỗi
        
        # Tạo index để tìm kiếm nhanh hơn
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_category ON documents(category)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_filename ON documents(filename)
        """)
        
        conn.commit()
        conn.close()
    
    def save_document(
        self,
        filename: str,
        file_data: bytes,
        file_type: str,
        category: str,
        document_type: Optional[str] = None,
        issuing_agency: Optional[str] = None,
        issue_date: Optional[str] = None,
        content_text: Optional[str] = None,
        classification_result: Optional[Dict] = None,
        analysis_result: Optional[Dict] = None
    ) -> int:
        """
        Lưu file vào database
        
        Args:
            filename: Tên file
            file_data: Dữ liệu file (bytes)
            file_type: Loại file (pdf, docx, txt)
            category: Nhóm phân loại
            document_type: Loại văn bản (thông tư, nghị định, luật, ...)
            issuing_agency: Cơ quan ban hành
            issue_date: Ngày ban hành (YYYY-MM-DD hoặc YYYY/MM/DD)
            content_text: Nội dung văn bản đã trích xuất
            classification_result: Kết quả phân loại
            analysis_result: Kết quả phân tích
            
        Returns:
            ID của document vừa lưu
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Chuyển dict thành JSON string để lưu
        classification_json = json.dumps(classification_result, ensure_ascii=False) if classification_result else None
        analysis_json = json.dumps(analysis_result, ensure_ascii=False) if analysis_result else None
        
        # Chuyển đổi issue_date về format chuẩn (YYYY-MM-DD) nếu có
        formatted_date = None
        if issue_date:
            # Thử parse các format khác nhau
            try:
                # Format: YYYY-MM-DD hoặc YYYY/MM/DD
                if '/' in issue_date:
                    parts = issue_date.split('/')
                    if len(parts) == 3:
                        formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"  # DD/MM/YYYY -> YYYY-MM-DD
                    else:
                        formatted_date = issue_date.replace('/', '-')
                else:
                    formatted_date = issue_date
            except:
                formatted_date = issue_date
        
        cursor.execute("""
            INSERT INTO documents 
            (filename, file_type, file_size, file_data, category, document_type, 
             issuing_agency, issue_date, content_text, 
             classification_result, analysis_result, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename,
            file_type,
            len(file_data),
            file_data,
            category,
            document_type,
            issuing_agency,
            formatted_date,
            content_text,
            classification_json,
            analysis_json,
            datetime.now(),
            datetime.now()
        ))
        
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return doc_id
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """
        Lấy thông tin và dữ liệu file từ database
        
        Args:
            doc_id: ID của document
            
        Returns:
            Dict chứa thông tin document hoặc None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents WHERE id = ?
        """, (doc_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_documents_by_category(self, category: str) -> List[Dict]:
        """
        Lấy danh sách documents theo category
        
        Args:
            category: Nhóm phân loại
            
        Returns:
            List các dict chứa thông tin documents
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, filename, file_type, file_size, category, document_type, 
                   issuing_agency, issue_date, created_at
            FROM documents 
            WHERE category = ?
            ORDER BY created_at DESC
        """, (category,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_all_documents(self) -> List[Dict]:
        """
        Lấy tất cả documents
        
        Returns:
            List các dict chứa thông tin documents
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, filename, file_type, file_size, category, document_type, 
                   issuing_agency, issue_date, created_at
            FROM documents 
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def delete_document(self, doc_id: int) -> bool:
        """
        Xóa document khỏi database
        
        Args:
            doc_id: ID của document
            
        Returns:
            True nếu xóa thành công
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM documents WHERE id = ?
        """, (doc_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def search_documents(self, keyword: str, category: Optional[str] = None) -> List[Dict]:
        """
        Tìm kiếm documents theo từ khóa
        
        Args:
            keyword: Từ khóa tìm kiếm
            category: Lọc theo category (optional)
            
        Returns:
            List các dict chứa thông tin documents
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT id, filename, file_type, file_size, category, document_type, 
                       issuing_agency, issue_date, created_at
                FROM documents 
                WHERE (filename LIKE ? OR content_text LIKE ?) AND category = ?
                ORDER BY created_at DESC
            """, (f'%{keyword}%', f'%{keyword}%', category))
        else:
            cursor.execute("""
                SELECT id, filename, file_type, file_size, category, document_type, 
                       issuing_agency, issue_date, created_at
                FROM documents 
                WHERE filename LIKE ? OR content_text LIKE ?
                ORDER BY created_at DESC
            """, (f'%{keyword}%', f'%{keyword}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_statistics(self) -> Dict:
        """
        Lấy thống kê về documents
        
        Returns:
            Dict chứa thống kê
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tổng số documents
        cursor.execute("SELECT COUNT(*) FROM documents")
        total = cursor.fetchone()[0]
        
        # Số documents theo category
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM documents 
            GROUP BY category
        """)
        
        by_category = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Tổng dung lượng
        cursor.execute("SELECT SUM(file_size) FROM documents")
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_documents': total,
            'by_category': by_category,
            'total_size': total_size
        }
    
    def _row_to_dict(self, row) -> Dict:
        """Chuyển row thành dict"""
        return dict(row)

