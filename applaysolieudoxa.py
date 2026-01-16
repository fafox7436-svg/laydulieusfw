import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# ================= CẤU HÌNH BAN ĐẦU =================
st.set_page_config(page_title="Tool Tra Cứu EVN SPC - V4.0", layout="wide")

# Hàm khởi tạo trình duyệt Chrome
def init_driver():
    try:
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless') # Bỏ comment nếu muốn chạy ẩn
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver
    except Exception as e:
        st.error(f"Lỗi không mở được Chrome: {e}")
        return None

# ================= HÀM XỬ LÝ TRA CỨU =================
def tra_cuu_chung(driver, ma_tra_cuu, config):
    """
    Hàm tra cứu thông tin text trên web
    """
    ket_qua = {
        "Ma_Dau_Vao": ma_tra_cuu,
        "Trang_Thai": "",
        "Du_Lieu_1": "", 
        "Du_Lieu_2": ""  
    }
    
    try:
        # 1. Tìm ô nhập liệu
        search_box = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, config['ID_INPUT']))
        )
        search_box.clear()
        search_box.send_keys(str(ma_tra_cuu))
        
        # 2. Bấm nút tìm kiếm
        try:
            # Ưu tiên tìm nút bấm theo XPath
            nut_tim = driver.find_element(By.XPATH, config['XPATH_BTN'])
            nut_tim.click()
        except:
            # Nếu không thấy nút thì thử Enter
            search_box.send_keys(Keys.RETURN)
        
        # 3. Chờ load
        time.sleep(2) 
        
        # 4. Lấy dữ liệu
        found_any = False
        
        # Lấy dữ liệu trường 1
        try:
            el1 = driver.find_element(By.XPATH, config['XPATH_RES_1'])
            ket_qua["Du_Lieu_1"] = el1.text
            found_any = True
        except:
            pass

        # Lấy dữ liệu trường 2 (nếu có cấu hình)
        if config.get('XPATH_RES_2'):
            try:
                el2 = driver.find_element(By.XPATH, config['XPATH_RES_2'])
                ket_qua["Du_Lieu_2"] = el2.text
                found_any = True
            except:
                pass
        
        if found_any:
            ket_qua["Trang_Thai"] = "Thành công"
        else:
            ket_qua["Trang_Thai"] = "Không tìm thấy / Lỗi XPath"

    except Exception as e:
        ket_qua["Trang_Thai"] = f"Lỗi: {str(e)}"
        
    return ket_qua

# ================= GIAO DIỆN CHÍNH =================
st.title("⚡ Tool Tra Cứu Đa Năng (SFW EVN) - V4.0")

# Khởi tạo session state để lưu trạng thái
if 'driver' not in st.session_state: st.session_state.driver = None
if 'df_modem' not in st.session_state: st.session_state.df_modem = None
if 'df_dcu' not in st.session_state: st.session_state.df_dcu = None

# --- SIDEBAR: NHẬP LIỆU & ĐIỀU KHIỂN ---
with st.sidebar:
    st.header("1. Nạp dữ liệu đầu vào")
    file_tram_cd = st.file_uploader("File Trạm CD", type=['xlsx', 'csv'])
    file_noi_bo = st.file_uploader("File Nội Bộ", type=['xlsx', 'csv'])

    df_input = None
    if file_tram_cd and file_noi_bo:
        try:
            # Đọc file (Hỗ trợ cả Excel và CSV)
            if file_tram_cd.name.endswith('.csv'): df1 = pd.read_csv(file_tram_cd)
            else: df1 = pd.read_excel(file_tram_cd)
            
            if file_noi_bo.name.endswith('.csv'): df2 = pd.read_csv(file_noi_bo)
            else: df2 = pd.read_excel(file_noi_bo)
            
            # Gộp list (Tìm cột SO_TBI)
            # Lưu ý: Cần kiểm tra đúng tên cột trong file của bạn
            col_name = 'SO_TBI' 
            if col_name not in df1.columns: 
                st.warning(f"Không tìm thấy cột '{col_name}' trong file Trạm CD, thử dùng cột đầu tiên.")
                col_name = df1.columns[0]
                
            list_ma = df1[col_name].dropna().astype(str).unique().tolist()
            
            if col_name in df2.columns:
                list_ma += df2[col_name].dropna().astype(str).unique().tolist()
            
            df_input = pd.DataFrame({'Code': list_ma})
            st.success(f"Đã nạp tổng cộng {len(df_input)} mã.")
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

    st.divider()
    st.header("2. Điều khiển Browser")
if st.button("Mở Trình Duyệt & Đăng Nhập", type="primary"):
        if st.session_state.driver is None:
            driver = init_driver()
            
            # Kiểm tra xem driver có mở thành công không
            if driver is not None:
                st.session_state.driver = driver
                try:
                    driver.get("https://sfw.evnspc.vn/")
                    st.info("Đã mở Chrome! Hãy đăng nhập thủ công rồi quay lại đây.")
                except Exception as e:
                    st.error(f"Không thể truy cập web. Lỗi: {e}")
            else:
                st.error("Không thể khởi động trình duyệt Chrome. Hãy đảm bảo bạn đang chạy trên máy tính cá nhân (Localhost), không phải trên Cloud.")
        else:
            st.warning("Trình duyệt đã mở rồi.")
            
# ================= TAB CHỨC NĂNG =================
tab1, tab2 = st.tabs(["📡 TRA CỨU MODEM", "🔋 TRA CỨU DCU & TẢI FILE"])

# --- TAB 1: MODEM ---
with tab1:
    st.markdown("### Quy trình: Đăng nhập -> Menu 'Quản lý Modem'")
    
    # Cấu hình XPath cho Modem
    with st.expander("⚙️ Cấu hình ID/XPath (Modem)", expanded=True):
        md_id_input = st.text_input("ID Ô nhập liệu", value="txtMaDiemDo", key="md1")
        md_xpath_btn = st.text_input("XPath Nút Tìm", value="//button[contains(text(),'Tìm kiếm')]", key="md2")
        md_xpath_res = st.text_input("XPath Ô Kết Quả (Status)", value="//table[@id='gridData']//tr[1]//td[5]", key="md3")

if st.button("🚀 Chạy Tra Cứu Modem"):
        # Kiểm tra điều kiện
        if not st.session_state.driver or df_input is None:
            st.error("Vui lòng mở trình duyệt và nạp file trước!")
        else:
            # === PHẦN NÀY PHẢI THỤT VÀO TRONG SO VỚI 'ELSE' ===
            config = {
                'ID_INPUT': md_id_input,
                'XPATH_BTN': md_xpath_btn,
                'XPATH_RES_1': md_xpath_res,
                'XPATH_RES_2': None
            }
            
            results = []
            bar = st.progress(0)
            status_text = st.empty()
            
            for i, row in df_input.iterrows():
                ma = row['Code']
                # Update thanh tiến trình
                bar.progress(int((i / len(df_input)) * 100))
                status_text.text(f"Đang xử lý: {ma} ({i+1}/{len(df_input)})")
                
                # Gọi hàm
                res = tra_cuu_chung(st.session_state.driver, ma, config)
                results.append(res)
            
            bar.progress(100)
            status_text.text("Hoàn tất!")
            st.session_state.df_modem = pd.DataFrame(results)



