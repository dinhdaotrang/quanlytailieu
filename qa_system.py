"""
Module hệ thống Q&A dựa trên tài liệu đã phân loại
"""

import os
from typing import List, Dict, Optional
from document_reader import DocumentReader
from classifier import DocumentClassifier
from config import Config
from database import DocumentDB

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class QASystem:
    """Hệ thống Q&A dựa trên tài liệu trong từng nhóm"""
    
    def __init__(self, db: Optional[DocumentDB] = None):
        self.reader = DocumentReader()
        self.classifier = DocumentClassifier()
        self.db = db
        self.client = None
        self._init_openai()
    
    def _init_openai(self):
        """Khởi tạo OpenAI client nếu có API key"""
        if not OPENAI_AVAILABLE:
            return
        
        api_key = Config.get_api_key()
        if api_key:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                print(f"Lỗi khởi tạo OpenAI client: {str(e)}")
    
    def get_documents_by_group(self, category: Optional[str] = None) -> List[Dict]:
        """
        Lấy danh sách tài liệu từ database hoặc filesystem
        
        Args:
            category: Tên category (nhóm) - None để lấy tất cả
            
        Returns:
            List các dict chứa thông tin tài liệu
        """
        documents = []
        
        # Ưu tiên dùng database nếu có
        if self.db:
            try:
                if category:
                    docs = self.db.get_documents_by_category(category)
                else:
                    docs = self.db.get_all_documents()
                
                # Lấy full content cho mỗi document
                for doc in docs:
                    full_doc = self.db.get_document(doc['id'])
                    if full_doc and full_doc.get('content_text'):
                        documents.append({
                            'id': doc['id'],
                            'filename': doc['filename'],
                            'content': full_doc['content_text'],
                            'category': doc['category'],
                            'document_type': doc.get('document_type'),
                            'issuing_agency': doc.get('issuing_agency'),
                            'issue_date': doc.get('issue_date')
                        })
            except Exception as e:
                print(f"Lỗi đọc từ database: {str(e)}")
        
        return documents
    
    def search_documents(self, question: str, category: Optional[str] = None, max_docs: int = 5) -> List[Dict]:
        """
        Tìm kiếm trong tài liệu
        
        Args:
            question: Câu hỏi
            category: Category (nhóm) - None để tìm trong tất cả
            max_docs: Số lượng tài liệu tối đa để tìm
            
        Returns:
            List các đoạn văn bản liên quan
        """
        documents = self.get_documents_by_group(category)
        if not documents:
            return []
        
        question_lower = question.lower()
        question_keywords = question_lower.split()
        
        results = []
        
        # Tìm kiếm đơn giản: tìm tài liệu có chứa từ khóa trong câu hỏi
        for doc in documents[:max_docs]:
            content_lower = doc['content'].lower()
            
            # Đếm số từ khóa xuất hiện
            matches = sum(1 for keyword in question_keywords if keyword in content_lower)
            
            if matches > 0:
                # Tìm đoạn văn bản chứa từ khóa
                paragraphs = doc['content'].split('\n')
                relevant_paragraphs = []
                
                for para in paragraphs:
                    para_lower = para.lower()
                    if any(keyword in para_lower for keyword in question_keywords) and len(para.strip()) > 20:
                        relevant_paragraphs.append(para.strip())
                
                if relevant_paragraphs:
                    result_item = {
                        'filename': doc['filename'],
                        'id': doc.get('id'),
                        'category': doc.get('category'),
                        'relevant_text': relevant_paragraphs[:3],  # Lấy 3 đoạn đầu tiên
                        'match_score': matches,
                        'full_content': doc['content']  # Thêm full content để dùng với OpenAI
                    }
                    # Thêm metadata nếu có
                    if doc.get('document_type'):
                        result_item['document_type'] = doc['document_type']
                    if doc.get('issuing_agency'):
                        result_item['issuing_agency'] = doc['issuing_agency']
                    if doc.get('issue_date'):
                        result_item['issue_date'] = doc['issue_date']
                    
                    results.append(result_item)
        
        # Sắp xếp theo điểm số
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return results
    
    def _answer_with_openai(self, question: str, context_docs: List[Dict]) -> Optional[str]:
        """
        Trả lời câu hỏi sử dụng OpenAI
        
        Args:
            question: Câu hỏi
            context_docs: Danh sách tài liệu context
            
        Returns:
            Câu trả lời hoặc None nếu lỗi
        """
        if not self.client or not context_docs:
            return None
        
        try:
            # Chuẩn bị context từ các tài liệu (giới hạn để không vượt quá token limit)
            context_parts = []
            total_length = 0
            max_context_length = 10000  # Giới hạn context để tiết kiệm token
            
            for doc in context_docs[:3]:  # Lấy top 3 tài liệu
                content = doc.get('full_content', '')
                if total_length + len(content) > max_context_length:
                    # Cắt bớt nếu quá dài
                    remaining = max_context_length - total_length
                    content = content[:remaining]
                    context_parts.append(f"\n\n=== {doc['filename']} ===\n{content}")
                    break
                else:
                    context_parts.append(f"\n\n=== {doc['filename']} ===\n{content}")
                    total_length += len(content)
            
            context = '\n'.join(context_parts)
            
            # Gọi OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Hoặc "gpt-3.5-turbo" để tiết kiệm hơn
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là trợ lý AI chuyên về tài liệu pháp lý, kỹ thuật, đầu tư của Việt Nam. "
                                   "Hãy trả lời câu hỏi dựa trên nội dung tài liệu được cung cấp. "
                                   "Nếu thông tin không có trong tài liệu, hãy nêu rõ 'Tài liệu hiện có chưa cung cấp thông tin này'. "
                                   "Trả lời bằng tiếng Việt, ngắn gọn, chính xác."
                    },
                    {
                        "role": "user",
                        "content": f"Dựa trên các tài liệu sau, hãy trả lời câu hỏi:\n\n"
                                  f"TÀI LIỆU:\n{context}\n\n"
                                  f"CÂU HỎI: {question}\n\n"
                                  f"Hãy trả lời dựa trên nội dung tài liệu trên."
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Lỗi khi gọi OpenAI API: {str(e)}")
            return None
    
    def answer_question(self, question: str, category: Optional[str] = None, use_openai: bool = True) -> Dict:
        """
        Trả lời câu hỏi dựa trên tài liệu
        
        Args:
            question: Câu hỏi
            category: Category (nhóm) - None thì tìm trong tất cả
            use_openai: Sử dụng OpenAI nếu có (mặc định True)
            
        Returns:
            Dict chứa câu trả lời và nguồn tham khảo
        """
        # Tìm tài liệu liên quan
        results = self.search_documents(question, category, max_docs=5)
        
        if not results:
            return {
                'answer': 'Tài liệu hiện có chưa cung cấp thông tin này.',
                'sources': [],
                'confidence': 'low',
                'method': 'simple'
            }
        
        # Nếu có OpenAI và muốn dùng, sử dụng OpenAI
        if use_openai and self.client:
            openai_answer = self._answer_with_openai(question, results)
            if openai_answer:
                sources = []
                for r in results[:3]:
                    source_info = {'filename': r['filename']}
                    if r.get('id'):
                        source_info['id'] = r['id']
                    if r.get('document_type'):
                        source_info['document_type'] = r['document_type']
                    if r.get('issuing_agency'):
                        source_info['issuing_agency'] = r['issuing_agency']
                    sources.append(source_info)
                
                return {
                    'answer': openai_answer,
                    'sources': sources,
                    'confidence': 'high',
                    'method': 'openai'
                }
        
        # Fallback: Tạo câu trả lời từ các đoạn văn bản liên quan
        answer_parts = []
        sources = []
        
        for result in results[:3]:  # Lấy top 3
            source_info = {'filename': result['filename']}
            if result.get('id'):
                source_info['id'] = result['id']
            if result.get('document_type'):
                source_info['document_type'] = result['document_type']
            sources.append(source_info)
            
            for text in result['relevant_text']:
                if text not in answer_parts:
                    answer_parts.append(text)
        
        answer = '\n\n'.join(answer_parts[:3])  # Giới hạn 3 đoạn
        
        return {
            'answer': answer,
            'sources': sources,
            'confidence': 'high' if len(results) >= 2 else 'medium',
            'method': 'simple'
        }
    
    def reload_openai_client(self):
        """Reload OpenAI client (sau khi cập nhật API key)"""
        self._init_openai()
