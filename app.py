"""
Streamlit App - Hệ thống phân loại và quản lý tài liệu
"""

import streamlit as st
import os
import shutil
from datetime import datetime
from document_reader import DocumentReader
from classifier import DocumentClassifier
from analyzer import DocumentAnalyzer
from qa_system import QASystem
from config import Config
from database import DocumentDB
from metadata_extractor import MetadataExtractor


# Cấu hình trang
st.set_page_config(
    page_title="Hệ thống Phân loại Tài liệu",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo các class
def init_components():
    db = DocumentDB()
    return {
        'reader': DocumentReader(),
        'classifier': DocumentClassifier(),
        'analyzer': DocumentAnalyzer(),
        'qa': QASystem(db=db),
        'db': db
    }

# Khởi tạo components
if 'components' not in st.session_state:
    st.session_state.components = init_components()

components = st.session_state.components

# Sidebar
with st.sidebar:
    st.title("📚 Hệ thống Phân loại Tài liệu")
    st.markdown("---")
    
    page = st.radio(
        "Chọn chức năng",
        ["📤 Upload & Phân loại", "📁 Quản lý Tài liệu"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### Thống kê")
    
    # Đếm số file trong mỗi thư mục
    folders = {
        'Metro/Đường sắt đô thị': 'Metro_DuongSatDoThi',
        'Đấu thầu/Khu giáo dục/TOD': 'DauThau_KhuGiaoDuc_TOD',
        'Chung cư': 'ChungCu',
        'Nhà ở xã hội': 'NhaO_XaHoi',
        'Khác': 'Khac'
    }
    
    # Lấy thống kê từ database
    try:
        stats = components['db'].get_statistics()
        by_category = stats.get('by_category', {})
        
        for name, folder in folders.items():
            count = by_category.get(folder, 0)
            st.metric(name, count)
    except:
        # Fallback nếu database chưa khởi tạo
        for name, folder in folders.items():
            count = 0
            if os.path.exists(folder):
                count = len([f for f in os.listdir(folder) 
                            if os.path.isfile(os.path.join(folder, f)) and 
                            f.lower().endswith(('.pdf', '.docx', '.txt'))])
            st.metric(name, count)
    
    st.markdown("---")
    st.markdown("### ⚙️ Cấu hình OpenAI")
    
    # Kiểm tra API key hiện tại
    current_api_key = Config.get_api_key()
    api_key_status = "✅ Đã cấu hình" if current_api_key else "❌ Chưa cấu hình"
    st.write(f"Trạng thái: {api_key_status}")
    
    # Input API key
    new_api_key = st.text_input(
        "OpenAI API Key",
        value=current_api_key if current_api_key else "",
        type="password",
        help="Nhập API key của bạn từ https://platform.openai.com/api-keys",
        placeholder="sk-..."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Lưu", use_container_width=True):
            if new_api_key and new_api_key.strip():
                # Lưu vào config file
                Config.save_api_key(new_api_key)
                # Lưu vào session state
                Config.save_to_session_state(new_api_key)
                # Reload QASystem
                components['qa'].reload_openai_client()
                st.success("✅ Đã lưu API key!")
                st.rerun()
            else:
                st.warning("Vui lòng nhập API key")
    
    with col2:
        if st.button("🔄 Kiểm tra", use_container_width=True):
            test_key = new_api_key if new_api_key else current_api_key
            if test_key:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=test_key)
                    # Test với một request đơn giản
                    client.models.list()
                    st.success("✅ API key hợp lệ!")
                except Exception as e:
                    st.error(f"❌ API key không hợp lệ: {str(e)}")
            else:
                st.warning("Chưa có API key để kiểm tra")
    
    if current_api_key:
        st.info("💡 Tip: Copy API key từ https://platform.openai.com/api-keys và paste vào ô trên")

# Main content
if page == "📤 Upload & Phân loại":
    st.title("📤 Upload & Phân loại Tài liệu")
    st.markdown("---")
    
    # Upload file
    uploaded_file = st.file_uploader(
        "Chọn file tài liệu (PDF, DOCX, TXT)",
        type=['pdf', 'docx', 'txt'],
        help="Hỗ trợ các định dạng: PDF, DOCX, TXT"
    )
    
    if uploaded_file is not None:
        # Lưu file tạm
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        temp_path = os.path.join(upload_dir, uploaded_file.name)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Hiển thị thông tin file
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tên file", uploaded_file.name)
        with col2:
            file_size = uploaded_file.size / 1024  # KB
            st.metric("Kích thước", f"{file_size:.2f} KB")
        with col3:
            st.metric("Định dạng", uploaded_file.type.split('/')[-1].upper())
        
        st.markdown("---")
        
        # Xử lý file
        with st.spinner("Đang đọc và phân tích tài liệu..."):
            try:
                # Đọc nội dung
                content, file_type = components['reader'].read_file(temp_path)
                
                # Phân loại
                classification = components['classifier'].classify(content, uploaded_file.name)
                
                # Phân tích (có thể dùng OpenAI nếu có API key)
                use_openai_analysis = Config.get_api_key() is not None
                analysis = components['analyzer'].analyze(
                    content, uploaded_file.name, classification, 
                    use_openai=use_openai_analysis
                )
                
                # Trích xuất metadata tự động
                auto_metadata = MetadataExtractor.extract_metadata(content, uploaded_file.name)
                
                # Hiển thị kết quả
                st.success("✅ Đã xử lý xong!")
                
                # Mapping nhóm (dùng chung cho cả app)
                folder_to_display = {
                    'Metro_DuongSatDoThi': '🔹 Metro/Đường sắt đô thị',
                    'DauThau_KhuGiaoDuc_TOD': '🔹 Đấu thầu/Khu giáo dục/TOD',
                    'ChungCu': '🔹 Chung cư',
                    'NhaO_XaHoi': '🔹 Nhà ở xã hội',
                    'Khac': '🔹 Khác'
                }
                
                display_to_folder = {
                    '🔹 Metro/Đường sắt đô thị': 'Metro_DuongSatDoThi',
                    '🔹 Đấu thầu/Khu giáo dục/TOD': 'DauThau_KhuGiaoDuc_TOD',
                    '🔹 Chung cư': 'ChungCu',
                    '🔹 Nhà ở xã hội': 'NhaO_XaHoi',
                    '🔹 Khác': 'Khac'
                }
                
                # Tab kết quả
                tab1, tab2, tab3 = st.tabs(["📊 Kết quả Phân loại", "📝 Phân tích Chi tiết", "📄 Nội dung"])
                
                with tab1:
                    st.subheader("Kết quả Phân loại")
                    
                    main_folder = classification['main_folder']
                    auto_selected_display = folder_to_display.get(main_folder, main_folder)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📊 Phân loại Tự động")
                        st.info(auto_selected_display)
                        
                        # Độ tin cậy
                        confidence_labels = {
                            'cao': '🟢 Cao',
                            'trung_binh': '🟡 Trung bình',
                            'thap': '🔴 Thấp'
                        }
                        st.metric("Độ tin cậy", confidence_labels.get(classification['confidence'], classification['confidence']))
                    
                    with col2:
                        if classification.get('sub_groups'):
                            st.markdown("### Nhóm phụ")
                            for sub in classification['sub_groups']:
                                st.write(f"- {sub['group']} (điểm: {sub['score']})")
                        else:
                            st.markdown("### Nhóm phụ")
                            st.write("Không có")
                    
                    # Từ khóa khớp
                    if classification.get('matched_keywords'):
                        st.markdown("### Từ khóa khớp")
                        keywords_str = ', '.join(classification['matched_keywords'][:10])
                        st.write(keywords_str)
                    
                    st.markdown("---")
                    st.markdown("### ✏️ Chọn Nhóm Phân Loại")
                    st.write("Bạn có thể chọn nhóm phân loại khác nếu cần:")
                    
                    # Dropdown để chọn nhóm
                    all_groups = list(folder_to_display.values())
                    # Lấy index mặc định từ session state hoặc từ auto classification
                    default_index = 0
                    if 'selected_folder' in st.session_state:
                        # Nếu đã chọn trước đó, dùng nhóm đó
                        prev_selected = folder_to_display.get(st.session_state.selected_folder)
                        if prev_selected and prev_selected in all_groups:
                            default_index = all_groups.index(prev_selected)
                    elif auto_selected_display in all_groups:
                        default_index = all_groups.index(auto_selected_display)
                    
                    selected_group_display = st.selectbox(
                        "Chọn nhóm để lưu tài liệu:",
                        all_groups,
                        index=default_index,
                        key=f"group_selector_{uploaded_file.name}",  # Unique key cho mỗi file
                        help="Mặc định là nhóm được hệ thống tự động phân loại. Bạn có thể chọn nhóm khác nếu cần."
                    )
                    
                    # Lưu vào session state để dùng khi lưu file
                    selected_folder_final = display_to_folder[selected_group_display]
                    st.session_state.selected_folder = selected_folder_final
                    
                    if selected_group_display != auto_selected_display:
                        st.warning(f"⚠️ Bạn đã chọn nhóm khác với kết quả tự động: **{selected_group_display}**")
                    else:
                        st.info(f"📌 Đang chọn nhóm: **{selected_group_display}** (theo kết quả tự động)")
                
                with tab2:
                    st.subheader("Phân tích Chi tiết")
                    
                    # Tóm tắt điều hành
                    st.markdown("### 📋 Tóm tắt điều hành")
                    st.info(analysis['executive_summary'])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Từ khóa nổi bật
                        if analysis['keywords']:
                            st.markdown("### 🔑 Từ khóa nổi bật")
                            keywords_display = ', '.join(analysis['keywords'][:10])
                            st.write(keywords_display)
                        
                        # Smart Tags
                        if analysis['tags']:
                            st.markdown("### 🏷️ Smart Tags")
                            tags_display = ' '.join([f"`{tag}`" for tag in analysis['tags']])
                            st.markdown(tags_display)
                    
                    with col2:
                        # Dự án & Địa danh
                        if analysis['projects']:
                            st.markdown("### 📍 Dự án")
                            for project in analysis['projects']:
                                st.write(f"- {project}")
                        
                        if analysis['locations']:
                            st.markdown("### 📍 Địa danh")
                            for loc in analysis['locations']:
                                st.write(f"- {loc}")
                    
                    # Mức độ bảo mật
                    security_labels = {
                        'cong_khai': '🟢 Công khai',
                        'noi_bo': '🟡 Nội bộ',
                        'nhay_cam': '🔴 Nhạy cảm',
                        'mat_chua_cong_bo': '🔴 Mật - chưa công bố'
                    }
                    st.markdown("### 🔒 Mức độ bảo mật")
                    st.warning(security_labels.get(analysis['security_level'], analysis['security_level']))
                    
                    # Gợi ý hành động
                    if analysis['action_suggestions']:
                        st.markdown("### 💡 Gợi ý hành động tiếp theo")
                        for suggestion in analysis['action_suggestions']:
                            st.write(f"• {suggestion}")
                
                with tab3:
                    st.subheader("Nội dung Tài liệu")
                    st.text_area("Nội dung", content, height=400, disabled=True)
                
                # Form nhập metadata
                st.markdown("---")
                st.markdown("### 📋 Thông tin Văn bản")
                
                # Trích xuất metadata tự động
                auto_metadata = MetadataExtractor.extract_metadata(content, uploaded_file.name)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Loại văn bản
                    document_types = ['', 'Nghị định', 'Nghị quyết', 'Thông tư', 'Luật', 
                                     'Quyết định', 'Chỉ thị', 'Thông báo', 'Công văn', 
                                     'Quy chế', 'Quy định', 'Khác']
                    
                    default_doc_type_idx = 0
                    if auto_metadata['document_type']:
                        try:
                            default_doc_type_idx = document_types.index(auto_metadata['document_type'])
                        except:
                            pass
                    
                    document_type = st.selectbox(
                        "Loại văn bản *",
                        document_types,
                        index=default_doc_type_idx,
                        help="Loại văn bản: Nghị định, Nghị quyết, Thông tư, Luật, ..."
                    )
                    
                    # Ngày ban hành
                    issue_date = st.text_input(
                        "Ngày ban hành (DD/MM/YYYY)",
                        value=auto_metadata['issue_date'] if auto_metadata['issue_date'] else "",
                        placeholder="Ví dụ: 19/02/2025",
                        help="Định dạng: DD/MM/YYYY hoặc DD-MM-YYYY"
                    )
                
                with col2:
                    # Cơ quan ban hành
                    issuing_agency = st.text_input(
                        "Cơ quan ban hành",
                        value=auto_metadata['issuing_agency'] if auto_metadata['issuing_agency'] else "",
                        placeholder="Ví dụ: Chính phủ, Bộ Xây dựng, ...",
                        help="Tên cơ quan ban hành văn bản"
                    )
                
                if auto_metadata['document_type'] or auto_metadata['issuing_agency'] or auto_metadata['issue_date']:
                    st.info("ℹ️ Hệ thống đã tự động điền một số thông tin từ tài liệu. Bạn có thể chỉnh sửa nếu cần.")
                
                # Nút lưu file
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    # Xác định thư mục đích (ưu tiên nhóm được chọn thủ công)
                    final_target_dir = st.session_state.get('selected_folder', classification['main_folder'])
                    final_target_display = folder_to_display.get(final_target_dir, final_target_dir)
                    
                    # Lấy giá trị từ form (có thể đã được chỉnh sửa)
                    document_type_final = document_type if document_type else None
                    issuing_agency_final = issuing_agency.strip() if issuing_agency.strip() else None
                    issue_date_final = issue_date.strip() if issue_date.strip() else None
                    
                    if st.button("✅ Lưu vào nhóm", type="primary", use_container_width=True):
                        # Lưu vào database
                        try:
                            # Đọc file data
                            with open(temp_path, "rb") as f:
                                file_data = f.read()
                            
                            # Lưu vào database với metadata đã điền
                            doc_id = components['db'].save_document(
                                filename=uploaded_file.name,
                                file_data=file_data,
                                file_type=file_type,
                                category=final_target_dir,
                                document_type=document_type_final,
                                issuing_agency=issuing_agency_final,
                                issue_date=issue_date_final,
                                content_text=content,
                                classification_result=classification,
                                analysis_result=analysis
                            )
                            
                            # Xóa file tạm
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            
                            st.success(f"✅ Đã lưu vào database: {final_target_display} (ID: {doc_id})")
                            
                            # Xóa selected_folder khỏi session state sau khi lưu
                            if 'selected_folder' in st.session_state:
                                del st.session_state.selected_folder
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Lỗi khi lưu vào database: {str(e)}")
                
                with col2:
                    if st.button("❌ Hủy", use_container_width=True):
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        st.rerun()
            
            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)

elif page == "📁 Quản lý Tài liệu":
    st.title("📁 Quản lý Tài liệu")
    st.markdown("---")
    
    # Chọn nhóm để xem
    selected_group_name = st.selectbox(
        "Chọn nhóm tài liệu",
        [
            "Tất cả",
            "Metro/Đường sắt đô thị",
            "Đấu thầu/Khu giáo dục/TOD",
            "Chung cư",
            "Nhà ở xã hội",
            "Khác"
        ]
    )
    
    group_folder_mapping = {
        "Tất cả": None,
        "Metro/Đường sắt đô thị": "Metro_DuongSatDoThi",
        "Đấu thầu/Khu giáo dục/TOD": "DauThau_KhuGiaoDuc_TOD",
        "Chung cư": "ChungCu",
        "Nhà ở xã hội": "NhaO_XaHoi",
        "Khác": "Khac"
    }
    
    selected_folder = group_folder_mapping[selected_group_name]
    
    # Lấy danh sách từ database
    try:
        if selected_folder:
            documents = components['db'].get_documents_by_category(selected_folder)
        else:
            documents = components['db'].get_all_documents()
        
        if documents:
            st.metric("Số lượng tài liệu", len(documents))
            st.markdown("---")
            
            # Hiển thị danh sách
            for i, doc in enumerate(documents, 1):
                doc_id = doc['id']
                filename = doc['filename']
                file_size = doc['file_size'] / 1024  # KB
                created_at = doc['created_at']
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{i}. {filename}**")
                    
                    # Hiển thị metadata nếu có
                    metadata_info = []
                    if doc.get('document_type'):
                        metadata_info.append(f"📄 {doc['document_type']}")
                    if doc.get('issuing_agency'):
                        metadata_info.append(f"🏛️ {doc['issuing_agency']}")
                    if doc.get('issue_date'):
                        metadata_info.append(f"📅 {doc['issue_date']}")
                    
                    if metadata_info:
                        st.caption(" | ".join(metadata_info))
                    else:
                        st.caption(f"Upload: {created_at}")
                
                with col2:
                    st.write(f"{file_size:.2f} KB")
                
                with col3:
                    # Nút tải xuống - lấy từ database
                    full_doc = components['db'].get_document(doc_id)
                    if full_doc:
                        file_data = full_doc['file_data']
                        
                        # Xác định MIME type dựa trên extension
                        file_ext = os.path.splitext(filename)[1].lower()
                        mime_types = {
                            '.pdf': 'application/pdf',
                            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            '.txt': 'text/plain'
                        }
                        mime_type = mime_types.get(file_ext, 'application/octet-stream')
                        
                        st.download_button(
                            label="📥 Tải xuống",
                            data=file_data,
                            file_name=filename,
                            mime=mime_type,
                            key=f"download_{doc_id}",
                            use_container_width=True
                        )
                
                with col4:
                    if st.button("🗑️ Xóa", key=f"delete_{doc_id}", use_container_width=True):
                        if components['db'].delete_document(doc_id):
                            st.success(f"Đã xóa: {filename}")
                            st.rerun()
                        else:
                            st.error("Lỗi khi xóa file")
        else:
            st.info("📂 Nhóm này chưa có tài liệu nào")
    except Exception as e:
        st.error(f"❌ Lỗi khi truy vấn database: {str(e)}")
        st.info("💡 Database có thể chưa được khởi tạo. Hãy upload một file để tạo database.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Hệ thống Phân loại Tài liệu - Trợ lý AI cấp điều hành"
    "</div>",
    unsafe_allow_html=True
)

