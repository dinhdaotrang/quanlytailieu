"""
Module trích xuất metadata từ tài liệu (loại văn bản, cơ quan ban hành, ngày ban hành)
"""

import re
from typing import Dict, Optional, Tuple
from datetime import datetime


class MetadataExtractor:
    """Class trích xuất metadata từ nội dung tài liệu"""
    
    # Các loại văn bản phổ biến
    DOCUMENT_TYPES = [
        'Nghị định',
        'Nghị quyết',
        'Thông tư',
        'Luật',
        'Quyết định',
        'Chỉ thị',
        'Thông báo',
        'Công văn',
        'Quy chế',
        'Quy định'
    ]
    
    # Các cơ quan ban hành phổ biến
    AGENCY_PATTERNS = [
        r'Chính\s+phủ',
        r'Quốc\s+hội',
        r'Bộ\s+[^,\n]+',
        r'Ủy\s+ban\s+[^,\n]+',
        r'Ban\s+[^,\n]+',
        r'Sở\s+[^,\n]+',
        r'UBND\s+[^,\n]+',
        r'HĐND\s+[^,\n]+',
        r'Thủ\s+tướng',
        r'Chủ\s+tịch'
    ]
    
    @staticmethod
    def extract_metadata(content: str, filename: str = "") -> Dict[str, Optional[str]]:
        """
        Trích xuất metadata từ nội dung tài liệu
        
        Args:
            content: Nội dung văn bản
            filename: Tên file
            
        Returns:
            Dict chứa document_type, issuing_agency, issue_date
        """
        content_lower = content.lower()
        
        # Trích xuất loại văn bản
        document_type = MetadataExtractor._extract_document_type(content, content_lower, filename)
        
        # Trích xuất cơ quan ban hành
        issuing_agency = MetadataExtractor._extract_issuing_agency(content, content_lower)
        
        # Trích xuất ngày ban hành
        issue_date = MetadataExtractor._extract_issue_date(content, content_lower)
        
        return {
            'document_type': document_type,
            'issuing_agency': issuing_agency,
            'issue_date': issue_date
        }
    
    @staticmethod
    def _extract_document_type(content: str, content_lower: str, filename: str) -> Optional[str]:
        """Trích xuất loại văn bản"""
        # Lấy 1000 ký tự đầu (thường có thông tin loại văn bản ở đầu)
        preview = content[:1000]
        preview_lower = preview.lower()
        
        # Tìm trong nội dung với nhiều pattern khác nhau
        for doc_type in MetadataExtractor.DOCUMENT_TYPES:
            patterns = [
                rf'{doc_type}\s+số\s+\d+',  # "Nghị định số 123"
                rf'{doc_type}\s+\d+',        # "Nghị định 123"
                rf'{doc_type}\s+[^\s]+',    # "Nghị định ..."
            ]
            for pattern in patterns:
                if re.search(pattern, preview, re.IGNORECASE):
                    return doc_type
        
        # Tìm trong tên file
        filename_lower = filename.lower()
        for doc_type in MetadataExtractor.DOCUMENT_TYPES:
            if doc_type.lower() in filename_lower:
                return doc_type
        
        return None
    
    @staticmethod
    def _extract_issuing_agency(content: str, content_lower: str) -> Optional[str]:
        """Trích xuất cơ quan ban hành"""
        # Lấy 1000 ký tự đầu (thường có thông tin cơ quan ban hành ở đầu)
        preview = content[:1000]
        
        # Tìm các pattern cơ quan ban hành
        for pattern in MetadataExtractor.AGENCY_PATTERNS:
            match = re.search(pattern, preview, re.IGNORECASE)
            if match:
                agency = match.group(0).strip()
                # Làm sạch: loại bỏ dấu phẩy, dấu chấm ở cuối
                agency = agency.rstrip('.,;:')
                # Loại bỏ các từ thừa
                agency = agency.replace('CỦA', '').replace('của', '').strip()
                # Giới hạn độ dài
                if len(agency) <= 200 and len(agency) > 3:
                    return agency
        
        # Tìm pattern "CỦA [cơ quan]" hoặc "của [cơ quan]"
        pattern_cua = r'(?:CỦA|của)\s+([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][^,\n.]+)'
        match = re.search(pattern_cua, preview, re.IGNORECASE)
        if match:
            agency = match.group(1).strip()
            agency = agency.rstrip('.,;:')
            if len(agency) <= 200 and len(agency) > 3:
                return agency
        
        return None
    
    @staticmethod
    def _extract_issue_date(content: str, content_lower: str) -> Optional[str]:
        """Trích xuất ngày ban hành"""
        # Lấy 1500 ký tự đầu (tăng để tìm ngày ban hành tốt hơn)
        preview = content[:1500]
        
        # Các pattern ngày tháng - ưu tiên các pattern có từ khóa "ban hành", "ngày"
        priority_patterns = [
            # ngày DD/MM/YYYY ban hành hoặc ban hành ngày DD/MM/YYYY
            r'(?:ban\s+hành|ngày)\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            # ngày DD tháng MM năm YYYY (tiếng Việt) - có từ "ban hành"
            r'(?:ban\s+hành|ngày)\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})',
        ]
        
        # Tìm với priority patterns trước
        for pattern in priority_patterns:
            matches = re.findall(pattern, preview, re.IGNORECASE)
            if matches:
                match = matches[0]
                if len(match) == 3:
                    # Chuyển về format DD/MM/YYYY
                    if len(match[2]) == 4:  # YYYY ở cuối
                        day, month, year = match[0], match[1], match[2]
                        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        
        # Các pattern ngày tháng thông thường
        date_patterns = [
            # DD/MM/YYYY hoặc DD-MM-YYYY
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            # YYYY/MM/DD hoặc YYYY-MM-DD
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            # DD tháng MM năm YYYY (tiếng Việt)
            r'(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})',
            # ngày DD tháng MM năm YYYY
            r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, preview, re.IGNORECASE)
            if matches:
                # Lấy match đầu tiên (thường là ngày ban hành)
                match = matches[0]
                if len(match) == 3:
                    # Chuyển về format DD/MM/YYYY
                    if len(match[2]) == 4:  # YYYY ở cuối (DD/MM/YYYY)
                        day, month, year = match[0], match[1], match[2]
                        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    else:  # YYYY ở đầu (YYYY/MM/DD)
                        day, month, year = match[2], match[1], match[0]
                        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        
        return None

