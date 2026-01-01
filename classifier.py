"""
Module phân loại tài liệu vào các nhóm theo nội dung
"""

from typing import Dict, Tuple
import re


class DocumentClassifier:
    """Class để phân loại tài liệu vào các nhóm"""
    
    # Từ khóa cho mỗi nhóm
    KEYWORDS = {
        'metro': [
            'metro', 'đường sắt đô thị', 'tuyến metro', 'tuyến đường sắt',
            'depot', 'nhà ga', 'RAMS', 'FEED', 'Pre-FS', 'FS', 'khảo sát',
            'thiết kế metro', 'vận hành metro', 'TOD', 'transit-oriented',
            'hạ tầng giao thông', 'đường ray', 'đoàn tàu', 'tàu điện',
            'MRT', 'urban rail', 'mass transit'
        ],
        'dau_thau': [
            'đấu thầu', 'mời thầu', 'hồ sơ dự thầu', 'đề xuất kỹ thuật',
            'đề xuất tài chính', 'nhà thầu', 'đấu thầu rộng rãi',
            'đàm phán cạnh tranh', 'khu giáo dục', 'đường Thống Nhất',
            'Suối Cây Sao', 'TOD4', 'quy hoạch', 'đầu tư', 'dự án',
            'thuyết minh dự án', 'hồ sơ mời thầu', 'PPP', 'BT', 'BOT'
        ],
        'chung_cu': [
            'chung cư', 'căn hộ', 'apartment', 'condominium', 'nhà ở cao tầng',
            'dự án chung cư', 'bán nhà', 'mua nhà', 'sổ đỏ chung cư',
            'pháp lý chung cư', 'thiết kế chung cư', 'xây dựng chung cư',
            'kinh doanh bất động sản', 'bán hàng chung cư'
        ],
        'nha_o_xa_hoi': [
            'nhà ở xã hội', 'NOXH', 'nhà ở công nhân', 'nhà ở cho người thu nhập thấp',
            'chính sách nhà ở xã hội', 'ưu đãi nhà ở', 'an sinh xã hội',
            'dự án an sinh', 'nhà ở cho người nghèo', 'social housing'
        ]
    }
    
    # Mapping từ keyword group sang thư mục
    FOLDER_MAPPING = {
        'metro': 'Metro_DuongSatDoThi',
        'dau_thau': 'DauThau_KhuGiaoDuc_TOD',
        'chung_cu': 'ChungCu',
        'nha_o_xa_hoi': 'NhaO_XaHoi'
    }
    
    @staticmethod
    def classify(content: str, filename: str = "") -> Dict:
        """
        Phân loại tài liệu dựa trên nội dung
        
        Args:
            content: Nội dung văn bản
            filename: Tên file (để tham khảo)
            
        Returns:
            Dict chứa thông tin phân loại
        """
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # Đếm số từ khóa xuất hiện cho mỗi nhóm
        scores = {}
        matches = {}
        
        for group, keywords in DocumentClassifier.KEYWORDS.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                # Tìm kiếm từ khóa trong nội dung
                pattern = re.escape(keyword.lower())
                count = len(re.findall(pattern, content_lower))
                if count > 0:
                    score += count
                    matched_keywords.append(keyword)
            
            # Kiểm tra trong tên file
            for keyword in keywords:
                if keyword.lower() in filename_lower:
                    score += 2
                    if keyword not in matched_keywords:
                        matched_keywords.append(keyword)
            
            scores[group] = score
            matches[group] = matched_keywords
        
        # Xác định nhóm chính (nhóm có điểm cao nhất)
        if not any(scores.values()):
            # Không tìm thấy từ khóa nào, xếp vào "Khác"
            main_group = 'khac'
            main_folder = 'Khac'
            confidence = 'thap'
        else:
            main_group = max(scores, key=scores.get)
            main_folder = DocumentClassifier.FOLDER_MAPPING.get(main_group, 'Khac')
            
            # Đánh giá độ tin cậy
            max_score = scores[main_group]
            total_score = sum(scores.values())
            
            if max_score >= 5 and max_score / max(total_score, 1) > 0.6:
                confidence = 'cao'
            elif max_score >= 2:
                confidence = 'trung_binh'
            else:
                confidence = 'thap'
        
        # Xác định nhóm phụ (nếu có)
        sub_groups = []
        sorted_groups = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for group, score in sorted_groups[1:3]:  # Lấy 2 nhóm tiếp theo
            if score > 0 and group != main_group:
                sub_groups.append({
                    'group': group,
                    'folder': DocumentClassifier.FOLDER_MAPPING.get(group, ''),
                    'score': score
                })
        
        return {
            'main_group': main_group,
            'main_folder': main_folder,
            'sub_groups': sub_groups,
            'confidence': confidence,
            'scores': scores,
            'matched_keywords': matches[main_group] if main_group != 'khac' else []
        }

