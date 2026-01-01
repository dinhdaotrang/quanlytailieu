"""
Module phân tích tài liệu và tạo tóm tắt, tags, đánh giá
"""

from typing import Dict, List, Optional
import re
from config import Config

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class DocumentAnalyzer:
    """Class để phân tích và tạo thông tin chi tiết về tài liệu"""
    
    # Smart tags mẫu
    COMMON_TAGS = [
        'phap_ly', 'dau_thau', 'FS', 'Pre-FS', 'FEED', 'PPP', 'TOD', 
        'quy_hoach', 'von_dau_tu', 'thiet_ke', 'xay_dung', 'vận_hành',
        'hop_dong', 'nghị_định', 'nghị_quyết', 'thông_tư', 'quyết_định',
        'báo_cáo', 'thuyết_minh', 'kế_hoạch', 'dự_án'
    ]
    
    @staticmethod
    def analyze(content: str, filename: str, classification: Dict, use_openai: bool = False) -> Dict:
        """
        Phân tích tài liệu và tạo các thông tin chi tiết
        
        Args:
            content: Nội dung văn bản
            filename: Tên file
            classification: Kết quả phân loại từ classifier
            use_openai: Sử dụng OpenAI cho tóm tắt tốt hơn (mặc định False)
            
        Returns:
            Dict chứa các thông tin phân tích
        """
        # Tạo tóm tắt điều hành
        summary = DocumentAnalyzer.create_executive_summary(content, classification, use_openai=use_openai)
        
        # Tạo từ khóa và tags
        keywords, tags = DocumentAnalyzer.extract_keywords_and_tags(content, classification)
        
        # Nhận diện dự án và địa danh
        projects, locations = DocumentAnalyzer.identify_projects_locations(content)
        
        # Đánh giá mức độ bảo mật
        security_level = DocumentAnalyzer.assess_security_level(content, filename)
        
        # Gợi ý hành động
        action_suggestions = DocumentAnalyzer.suggest_actions(classification, keywords)
        
        return {
            'executive_summary': summary,
            'keywords': keywords,
            'tags': tags,
            'projects': projects,
            'locations': locations,
            'security_level': security_level,
            'action_suggestions': action_suggestions
        }
    
    @staticmethod
    def create_executive_summary_with_openai(content: str, classification: Dict) -> Optional[str]:
        """Tạo tóm tắt điều hành sử dụng OpenAI"""
        if not OPENAI_AVAILABLE:
            return None
        
        api_key = Config.get_api_key()
        if not api_key:
            return None
        
        try:
            client = OpenAI(api_key=api_key)
            
            # Đọc toàn bộ văn bản (không giới hạn)
            full_content = content
            
            main_group = classification.get('main_group', 'khac')
            group_names = {
                'metro': 'Metro/Đường sắt đô thị',
                'dau_thau': 'Đấu thầu/Khu giáo dục/TOD',
                'chung_cu': 'Chung cư',
                'nha_o_xa_hoi': 'Nhà ở xã hội',
                'khac': 'Khác'
            }
            group_name = group_names.get(main_group, 'Khác')
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là trợ lý AI chuyên tóm tắt tài liệu pháp lý, kỹ thuật, đầu tư của Việt Nam. "
                                   "Hãy đọc toàn bộ văn bản và tạo tóm tắt điều hành ngắn gọn 5-7 dòng, "
                                   "tập trung vào thông tin quan trọng nhất như: nội dung chính, mục đích, "
                                   "phạm vi áp dụng, quy định quan trọng. "
                                   "Trả lời bằng tiếng Việt, ngắn gọn và chính xác."
                    },
                    {
                        "role": "user",
                        "content": f"Tài liệu này được phân loại vào nhóm: {group_name}.\n\n"
                                  f"Hãy đọc TOÀN BỘ văn bản sau và tạo tóm tắt điều hành (5-7 dòng):\n\n"
                                  f"{'='*50}\n{full_content}\n{'='*50}"
                    }
                ],
                temperature=0.3,
                max_tokens=500  # Tăng max_tokens để có thể tóm tắt đầy đủ hơn
            )
            
            summary = response.choices[0].message.content.strip()
            return f"Tài liệu thuộc nhóm: {group_name}. {summary}"
        
        except Exception as e:
            print(f"Lỗi khi tạo tóm tắt với OpenAI: {str(e)}")
            return None
    
    @staticmethod
    def create_executive_summary(content: str, classification: Dict, use_openai: bool = False) -> str:
        """Tạo tóm tắt điều hành 5-7 dòng"""
        # Thử dùng OpenAI nếu được yêu cầu
        if use_openai:
            openai_summary = DocumentAnalyzer.create_executive_summary_with_openai(content, classification)
            if openai_summary:
                return openai_summary
        # Lấy đoạn đầu tiên có ý nghĩa
        paragraphs = [p.strip() for p in content.split('\n') if len(p.strip()) > 50]
        
        if not paragraphs:
            paragraphs = [content[:500] if len(content) > 500 else content]
        
        # Lấy 1-2 đoạn đầu
        summary_text = ' '.join(paragraphs[:2])
        
        # Rút gọn nếu quá dài
        if len(summary_text) > 400:
            summary_text = summary_text[:400] + "..."
        
        # Thêm thông tin về phân loại
        main_group = classification.get('main_group', 'khac')
        group_names = {
            'metro': 'Metro/Đường sắt đô thị',
            'dau_thau': 'Đấu thầu/Khu giáo dục/TOD',
            'chung_cu': 'Chung cư',
            'nha_o_xa_hoi': 'Nhà ở xã hội',
            'khac': 'Khác'
        }
        group_name = group_names.get(main_group, 'Khác')
        
        summary = f"Tài liệu thuộc nhóm: {group_name}. {summary_text}"
        return summary
    
    @staticmethod
    def extract_keywords_and_tags(content: str, classification: Dict) -> tuple[List[str], List[str]]:
        """Trích xuất từ khóa và tags"""
        content_lower = content.lower()
        
        # Từ khóa từ phân loại
        keywords = classification.get('matched_keywords', [])
        
        # Tags dựa trên từ khóa và nội dung
        tags = []
        
        # Kiểm tra các tags phổ biến
        for tag in DocumentAnalyzer.COMMON_TAGS:
            if tag.replace('_', ' ') in content_lower or tag.replace('_', '') in content_lower:
                tags.append(tag)
        
        # Thêm tags từ phân loại
        main_group = classification.get('main_group', '')
        if main_group:
            tags.append(main_group)
        
        # Trích xuất các từ khóa quan trọng khác (tên dự án, số nghị định, v.v.)
        # Tìm số nghị định/quyết định
        pattern_nd = r'nghị\s*định\s*số\s*(\d+[^\s]*)'
        pattern_qd = r'quyết\s*định\s*số\s*(\d+[^\s]*)'
        pattern_tt = r'thông\s*tư\s*số\s*(\d+[^\s]*)'
        
        for pattern, prefix in [(pattern_nd, 'ND'), (pattern_qd, 'QD'), (pattern_tt, 'TT')]:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                for match in matches[:2]:  # Lấy tối đa 2
                    keywords.append(f"{prefix} {match}")
        
        # Loại bỏ trùng lặp
        keywords = list(dict.fromkeys(keywords))[:10]  # Giới hạn 10 từ khóa
        tags = list(dict.fromkeys(tags))
        
        return keywords, tags
    
    @staticmethod
    def identify_projects_locations(content: str) -> tuple[List[str], List[str]]:
        """Nhận diện dự án và địa danh"""
        projects = []
        locations = []
        
        # Một số địa danh và dự án phổ biến
        common_locations = [
            'Hà Nội', 'TP.HCM', 'TP Hồ Chí Minh', 'Bình Dương', 'Đồng Nai',
            'Long An', 'Cần Thơ', 'Đà Nẵng', 'Hải Phòng'
        ]
        
        common_projects = [
            'Tuyến 1', 'Tuyến 2', 'Tuyến 3', 'Metro Line', 'TOD',
            'Suối Cây Sao', 'Đường Thống Nhất', 'TOD4'
        ]
        
        content_normalized = content
        
        for loc in common_locations:
            if loc in content:
                locations.append(loc)
        
        for proj in common_projects:
            if proj in content:
                projects.append(proj)
        
        # Tìm các dự án có format "Dự án..." hoặc "Tuyến..."
        pattern_project = r'(dự\s*án|tuyến|metro\s*line)\s+[A-Z0-9\s]+'
        project_matches = re.findall(pattern_project, content, re.IGNORECASE)
        projects.extend([p.strip() for p in project_matches[:3]])
        
        # Loại bỏ trùng lặp
        projects = list(dict.fromkeys(projects))
        locations = list(dict.fromkeys(locations))
        
        return projects, locations
    
    @staticmethod
    def assess_security_level(content: str, filename: str) -> str:
        """Đánh giá mức độ bảo mật"""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # Từ khóa nhạy cảm
        sensitive_keywords = [
            'mật', 'bảo mật', 'bí mật', 'nội bộ', 'không công bố',
            'confidential', 'internal', 'secret'
        ]
        
        # Từ khóa công khai
        public_keywords = [
            'công khai', 'phổ biến', 'thông báo', 'công bố'
        ]
        
        for keyword in sensitive_keywords:
            if keyword in content_lower or keyword in filename_lower:
                return 'nhay_cam'
        
        # Kiểm tra nếu có "nội bộ" hoặc "dự thảo"
        if 'nội bộ' in content_lower or 'dự thảo' in content_lower:
            return 'noi_bo'
        
        for keyword in public_keywords:
            if keyword in content_lower:
                return 'cong_khai'
        
        # Mặc định: nội bộ nếu không có dấu hiệu gì
        return 'noi_bo'
    
    @staticmethod
    def suggest_actions(classification: Dict, keywords: List[str]) -> List[str]:
        """Gợi ý hành động tiếp theo"""
        suggestions = []
        main_group = classification.get('main_group', '')
        
        # Gợi ý dựa trên nhóm
        group_actions = {
            'metro': [
                'Chuyển cho phòng kỹ thuật Metro',
                'Kiểm tra tính đồng bộ với các tuyến khác',
                'Xem xét yêu cầu FS/Pre-FS/FEED'
            ],
            'dau_thau': [
                'Chuyển cho phòng đấu thầu',
                'Kiểm tra hồ sơ pháp lý dự án',
                'Xem xét tiến độ đấu thầu'
            ],
            'chung_cu': [
                'Chuyển cho phòng kinh doanh',
                'Kiểm tra pháp lý dự án',
                'Xem xét hồ sơ bán hàng'
            ],
            'nha_o_xa_hoi': [
                'Chuyển cho phòng an sinh xã hội',
                'Kiểm tra chính sách ưu đãi',
                'Xem xét quy trình phê duyệt'
            ]
        }
        
        if main_group in group_actions:
            suggestions.extend(group_actions[main_group])
        
        # Gợi ý dựa trên từ khóa
        keyword_lower = [k.lower() for k in keywords]
        
        if any('fs' in k or 'feed' in k for k in keyword_lower):
            suggestions.append('Kiểm tra đầy đủ hồ sơ FS/FEED')
        
        if any('phap_ly' in k or 'pháp lý' in k for k in keyword_lower):
            suggestions.append('Rà soát tính pháp lý của tài liệu')
        
        if any('dau_thau' in k or 'đấu thầu' in k for k in keyword_lower):
            suggestions.append('Cập nhật tiến độ đấu thầu')
        
        # Loại bỏ trùng lặp
        suggestions = list(dict.fromkeys(suggestions))
        
        return suggestions[:5]  # Giới hạn 5 gợi ý

