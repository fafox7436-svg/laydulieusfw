import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ================= CẤU HÌNH GIAO DIỆN =================
st.set_page_config(page_title="Tool Tra Cứu EVN SPC - V5.0 Final", layout="wide")

# ================= HÀM KHỞI TẠO TRÌNH DUYỆT =================
def init_driver():
    try:
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless') # Chạy ẩn (bỏ comment nếu cần)
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver
    except Exception as e:
        st.error(f"Lỗi mở Chrome: {e}. Hãy đảm bảo bạn đã cài Chrome và chạy trên máy tính cá nhân.")
        return None

# ================= HÀM TỰ ĐỘNG ĐĂNG NHẬP =================
def auto_login(driver, username, password):
    """
    Hàm tự động điền User/Pass và nhấn Enter
    """
    try:
        driver.get("https://sfw.evnspc.vn/")
        time.sleep(2) # Chờ web tải
        
        # 1. Điền Tên đăng nhập (ID: txtusername)
        try:
            user_box = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "txtusername"))
            )
            user_box.clear()
            user_box.send_keys(username)
        except:
            return False, "Không tìm thấy ô nhập User (txtusername)"

        # 2. Điền Mật khẩu (ID: txtpassword)
        try:
            pass_box = driver.find_element(By.ID, "txtpassword")
            pass_box.clear()
            pass_box.send_keys(password)
            
            # 3. Nhấn Enter để đăng nhập
            pass_box.send_keys(Keys.RETURN)
        except:
             return False, "Không tìm thấy ô nhập Pass (txtpassword)"
            
        return True, "Đã gửi lệnh đăng nhập!"
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}"

# ================= HÀM TRA CỨU DỮ LIỆU =================
def tra_cuu_chung(driver, ma_tra_cuu, config):
    ket_qua = {
        "Ma_Dau_Vao": ma_tra_cuu,
        "Trang_Thai": "",
        "Du_Lieu_1": "", 
        "Du_Lieu_2": ""  
    }
    
    try:
        # 1. Tìm ô nhập mã
        search_box = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, config['ID_INPUT']))
        )
        search_box.clear()
        search_box.send_keys(str(ma_tra_cuu))
        
        # 2. Bấm nút tìm kiếm (hoặc Enter)
        try:
            nut_tim = driver.find_element(By.XPATH, config['XPATH_BTN'])
            nut_tim.click()
        except:
            search_box.send_keys(Keys.RETURN)
        
        # 3. Chờ dữ liệu tải
        time.sleep(2) 
        
        # 4. Lấy dữ liệu
        found_any = False
        
        # Lấy cột 1
        try:
            el1 = driver.find_element(By.XPATH, config['XPATH_RES_1'])
            ket_qua["Du_Lieu_1"] = el1.text
            found_any = True
        except:
            pass

        # Lấy cột 2 (nếu có yêu cầu)
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
            ket_qua["Trang_Thai"] = "Không tìm thấy"

    except Exception as e:
        ket_qua["Trang_Thai"] = f"Lỗi: {str(e)}"
        
    return ket_qua

# ================= GIAO DIỆN CHÍNH (STREAMLIT) =================
st.title("⚡ Tool Tra Cứu SFW - V5.0 (Auto Login & Download)")

# Khởi tạo session state
if 'driver' not in st.session_state: st.session_state.driver = None
if 'df_modem' not in st.session_state: st.session_state.df_modem = None
if 'df_dcu' not in st.session_state: st.session_state.df_dcu = None

# --- SIDEBAR: CẤU HÌNH & INPUT ---
with st.sidebar:
    st.header("1. Đăng Nhập Hệ Thống")
    user_input = st.text_input("Tên đăng nhập SFW")
    pass_input = st.text_input("Mật khẩu SFW", type="password")
    
    st.divider()
    st.header("2. Nạp File Dữ Liệu")
    file_tram_cd = st.file_uploader("File Trạm CD", type=['xlsx', 'csv'])
    file_noi_bo = st.file_uploader("File Nội Bộ", type=['xlsx', 'csv'])

    df_input = None
    if file_tram_cd and file_noi_bo:
        try:
            # Đọc file
            if file_tram_cd.name.endswith('.csv'): df1 = pd.read_csv(file_tram_cd)
            else: df1 = pd.read_excel(file_tram_cd)
            
            if file_noi_bo.name.endswith('.csv'): df2 = pd.read_csv(file_noi_bo)
            else: df2 = pd.read_excel(file_noi_bo)
            
            # Tìm cột chứa Mã (Ưu tiên 'SO_TBI' hoặc cột đầu tiên)
            col_target = 'SO_TBI'
            if col_target not in df1.columns: 
                col_target = df1.columns[0]
                
            list_ma = df1[col_target].dropna().astype(str).unique().tolist()
            
            if col_target in df2.columns:
                list_ma += df2[col_target].dropna().astype(str).unique().tolist()
            elif len(df2.columns) > 0: # Fallback cột 0 của file 2
                 list_ma += df2.iloc[:, 0].dropna().astype(str).unique().tolist()
            
            df_input = pd.DataFrame({'Code': list_ma})
            st.success(f"Đã nạp {len(df_input)} mã cần tra.")
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

    st.divider()
    st.header("3. Điều Khiển")
    
    # NÚT: MỞ BROWSER & ĐĂNG NHẬP
    if st.button("🌐 Mở Web & Đăng Nhập Ngay", type="primary"):
        if st.session_state.driver is None:
            driver = init_driver()
            if driver:
                st.session_state.driver = driver
                # Gọi hàm login
                status, msg = auto_login(driver, user_input, pass_input)
                if status:
                    st.success(f"{msg} Hãy kiểm tra trình duyệt xem đã vào được chưa!")
                else:
                    st.error(msg)
        else:
            st.warning("Trình duyệt đang mở rồi.")

# ================= TAB CHỨC NĂNG =================
tab1, tab2 = st.tabs(["📡 TRA CỨU MODEM", "🔋 TRA CỨU DCU"])

# --- TAB 1: MODEM ---
with tab1:
    st.info("Lưu ý: Vào menu 'Quản lý Modem' trước khi bấm chạy.")
    
    with st.expander("Cấu hình ID/XPath (Modem)", expanded=True):
        md_id_input = st.text_input("ID Ô nhập liệu", value="txtMaDiemDo", key="md1")
        md_xpath_btn = st.text_input("XPath Nút Tìm", value="//button[contains(text(),'Tìm kiếm')]", key="md2")
        md_xpath_res = st.text_input("XPath Ô Kết Quả", value="//table[@id='gridData']//tr[1]//td[5]", key="md3")

    if st.button("🚀 Chạy Tra Cứu Modem"):
        if not st.session_state.driver or df_input is None:
            st.error("Chưa mở trình duyệt hoặc chưa có file!")
        else:
            config = {
                'ID_INPUT': md_id_input,
                'XPATH_BTN': md_xpath_btn,
                'XPATH_RES_1': md_xpath_res,
                'XPATH_RES_2': None
            }
            
            results = []
            bar = st.progress(0)
            log_text = st.empty()
            
            for i, row in df_input.iterrows():
                ma = row['Code']
                bar.progress(int((i / len(df_input)) * 100))
                log_text.text(f"Đang xử lý: {ma}")
                
                res = tra_cuu_chung(st.session_state.driver, ma, config)
                results.append(res)
            
            bar.progress(100)
            log_text.text("Hoàn tất!")
            st.session_state.df_modem = pd.DataFrame(results)

    if st.session_state.df_modem is not None:
        st.dataframe(st.session_state.df_modem)
        st.download_button("Tải Kết Quả Modem (CSV)", st.session_state.df_modem.to_csv(index=False).encode('utf-8-sig'), "KQ_Modem.csv")

# --- TAB 2: DCU ---
with tab2:
    st.info("Lưu ý: Vào menu 'Quản lý DCU' trước khi bấm chạy.")
    
    with st.expander("Cấu hình ID/XPath (DCU)", expanded=True):
        col1, col2 = st.columns(2)
        dcu_id_input = st.text_input("ID Ô nhập liệu", value="txtMaDiemDo", key="dcu1")
        dcu_xpath_btn = st.text_input("XPath Nút Tìm", value="//button[contains(text(),'Tìm kiếm')]", key="dcu2")
        with col1:
            dcu_xpath_res1 = st.text_input("XPath Cột DCU", value="//table[@id='gridData']//tr[1]//td[4]", key="dcu3")
        with col2:
            dcu_xpath_res2 = st.text_input("XPath Cột CTT", value="//table[@id='gridData']//tr[1]//td[6]", key="dcu4")
    
    st.write("---")
    # TÙY CHỌN TẢI FILE
    auto_download = st.checkbox("Tự động tải file Excel về máy?", value=False)
    id_nut_export = "bntexport" # ID bạn cung cấp

    if st.button("🚀 Chạy Tra Cứu DCU"):
        if not st.session_state.driver or df_input is None:
            st.error("Chưa mở trình duyệt hoặc chưa có file!")
        else:
            config = {
                'ID_INPUT': dcu_id_input,
                'XPATH_BTN': dcu_xpath_btn,
                'XPATH_RES_1': dcu_xpath_res1,
                'XPATH_RES_2': dcu_xpath_res2
            }
            
            results = []
            bar = st.progress(0)
            log_text = st.empty()
            driver = st.session_state.driver
            
            for i, row in df_input.iterrows():
                ma = row['Code']
                bar.progress(int((i / len(df_input)) * 100))
                log_text.text(f"Đang xử lý: {ma}")
                
                # 1. Lấy dữ liệu Text
                res = tra_cuu_chung(driver, ma, config)
                res['Ma_DCU'] = res.pop('Du_Lieu_1')
                res['Ma_Cong_To_Tong'] = res.pop('Du_Lieu_2')
                
                # 2. Bấm nút tải file (Nếu chọn)
                msg_dl = ""
                if auto_download and res['Trang_Thai'] == "Thành công":
                    try:
                        # Dùng Javascript click vào ID 'bntexport'
                        driver.execute_script(f"document.getElementById('{id_nut_export}').click();")
                        res['Trang_Thai_Tai_File'] = "Đã tải"
                        time.sleep(1.5) # Chờ tải
                    except:
                        res['Trang_Thai_Tai_File'] = "Lỗi nút tải"
                else:
                     res['Trang_Thai_Tai_File'] = "-"
                
                results.append(res)

            bar.progress(100)
            log_text.text("Hoàn tất!")
            st.session_state.df_dcu = pd.DataFrame(results)

    if st.session_state.df_dcu is not None:
        st.dataframe(st.session_state.df_dcu)
        st.download_button("Tải Kết Quả DCU (CSV)", st.session_state.df_dcu.to_csv(index=False).encode('utf-8-sig'), "KQ_DCU.csv")
