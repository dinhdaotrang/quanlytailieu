"""
Module đọc và xử lý các file tài liệu (PDF, DOCX, TXT)
"""

import os
from typing import Optional
import PyPDF2
from docx import Document


class DocumentReader:
    """Class để đọc nội dung từ các file PDF, DOCX, TXT"""
    
    @staticmethod
    def read_file(file_path: str) -> tuple[str, str]:
        """
        Đọc nội dung từ file
        
        Args:
            file_path: Đường dẫn đến file
            
        Returns:
            tuple: (nội dung văn bản, loại file)
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return DocumentReader.read_pdf(file_path), 'pdf'
        elif file_ext == '.docx':
            return DocumentReader.read_docx(file_path), 'docx'
        elif file_ext == '.txt':
            return DocumentReader.read_txt(file_path), 'txt'
        else:
            raise ValueError(f"Định dạng file không được hỗ trợ: {file_ext}")
    
    @staticmethod
    def read_pdf(file_path: str) -> str:
        """Đọc nội dung từ file PDF"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Lỗi khi đọc PDF: {str(e)}")
        return text.strip()
    
    @staticmethod
    def read_docx(file_path: str) -> str:
        """Đọc nội dung từ file DOCX"""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Lỗi khi đọc DOCX: {str(e)}")
    
    @staticmethod
    def read_txt(file_path: str) -> str:
        """Đọc nội dung từ file TXT"""
        try:
            # Thử các encoding khác nhau
            encodings = ['utf-8', 'utf-8-sig', 'cp1258', 'latin-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read().strip()
                except UnicodeDecodeError:
                    continue
            raise Exception("Không thể đọc file với các encoding đã thử")
        except Exception as e:
            raise Exception(f"Lỗi khi đọc TXT: {str(e)}")

