"""
Module quản lý cấu hình và API key
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv

# Load .env file nếu có
load_dotenv()

CONFIG_FILE = "config.json"
USE_DATABASE = True  # True: lưu vào database, False: lưu vào filesystem


class Config:
    """Class quản lý cấu hình và API key"""
    
    @staticmethod
    def get_api_key() -> Optional[str]:
        """
        Lấy API key từ các nguồn theo thứ tự ưu tiên:
        1. Session state (nếu đang chạy Streamlit)
        2. Environment variable
        3. Config file
        """
        # Thử từ session state (Streamlit)
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and 'openai_api_key' in st.session_state:
                api_key = st.session_state.openai_api_key
                if api_key and api_key.strip():
                    return api_key.strip()
        except:
            pass
        
        # Thử từ environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return api_key.strip()
        
        # Thử từ config file
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    api_key = config.get('openai_api_key')
                    if api_key:
                        return api_key.strip()
            except:
                pass
        
        return None
    
    @staticmethod
    def save_api_key(api_key: str) -> bool:
        """
        Lưu API key vào config file
        
        Args:
            api_key: API key cần lưu
            
        Returns:
            True nếu lưu thành công
        """
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except:
                    pass
            
            config['openai_api_key'] = api_key.strip()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Lỗi lưu API key: {str(e)}")
            return False
    
    @staticmethod
    def save_to_session_state(api_key: str):
        """Lưu API key vào Streamlit session state"""
        try:
            import streamlit as st
            st.session_state.openai_api_key = api_key.strip()
        except:
            pass

