import streamlit as st
import requests
import os
import threading
import uvicorn
import time
from dotenv import load_dotenv

# Load local .env if exists
load_dotenv()

import subprocess
import sys

# Start FastAPI backend in a background subprocess if it is not already running
def start_backend():
    try:
        log_file = open("backend.log", "a")
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=log_file,
            stderr=log_file
        )
    except Exception as e:
        print(f"Backend subprocess error: {e}")

try:
    requests.get("http://127.0.0.1:8000/courses", timeout=0.5)
except Exception:
    start_backend()
    time.sleep(2.5)  # Wait for uvicorn to bind to port 8000




# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="AI-LMS | Yapay Zeka Destekli Öğrenme Yönetim Sistemi",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://127.0.0.1:8000"

# Initialize Session State
if "user" not in st.session_state:
    st.session_state.user = None
if "api_key_gemini" not in st.session_state:
    st.session_state.api_key_gemini = os.getenv("GEMINI_API_KEY", "")
if "api_key_groq" not in st.session_state:
    st.session_state.api_key_groq = os.getenv("GROQ_API_KEY", "")
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = "groq"

# ==========================================
# Premium Custom CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #1a1e36 0%, #0d1021 100%);
        color: #e2e8f0;
    }
    
    /* Premium Title styling */
    .main-title {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
    }
    
    .course-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.05) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .course-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    /* Metric & Badge styling */
    .grade-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .grade-high {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .grade-mid {
        background-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    .grade-low {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    
    /* Buttons styling override */
    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: opacity 0.2s ease;
    }
    div.stButton > button:hover {
        opacity: 0.9;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# API Helper Functions
# ==========================================
def check_backend_status():
    try:
        response = requests.get(f"{API_BASE_URL}/courses", timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        return False

def get_headers():
    provider = st.session_state.selected_provider
    key = st.session_state.api_key_gemini if provider == "gemini" else st.session_state.api_key_groq
    return {"X-API-Key": key}

# ==========================================
# Sidebar UI & Authentication State
# ==========================================
with st.sidebar:
    st.markdown("## 🎓 AI-LMS Ayarları")
    
    # Check Backend Connection
    is_connected = check_backend_status()
    if is_connected:
        st.success("🟢 API Sunucusu Bağlı")
    else:
        st.error("🔴 API Sunucusu Çevrimdışı")
        st.info("Lütfen terminalde backend sunucuyu başlatın:\n`uvicorn api:app --reload`")
    
    st.divider()
    
    # LLM Settings
    st.markdown("### 🤖 Yapay Zeka Servisi")
    provider = st.selectbox(
        "Sağlayıcı Seçin", 
        ["gemini", "groq"], 
        index=0 if st.session_state.selected_provider == "gemini" else 1,
        key="selected_provider_selectbox"
    )
    st.session_state.selected_provider = provider
        
    st.divider()
    
    # Authentication View or Logout
    if st.session_state.user:
        st.markdown(f"**Giriş Yapıldı:**\n👤 `{st.session_state.user['username']}` ({st.session_state.user['role'].upper()})")
        if st.button("Çıkış Yap"):
            st.session_state.user = None
            st.rerun()
    else:
        st.markdown("🔒 Hesap Girişi / Kayıt")

# ==========================================
# Login / Register View
# ==========================================
def render_auth_page():
    st.markdown("<h1 class='main-title'>🎓 Yapay Zeka Destekli LMS</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Yapay Zeka Destekli Kurs Oluşturma, İçerik Özetleme ve Akıllı Ödev Değerlendirme Sistemi</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class='glass-card'>
            <h3>Sistem Yetenekleri</h3>
            <ul>
                <li><b>📚 Kurs ve Ders Yönetimi:</b> Eğitmenler için kolay kurs müfredatı tasarımı.</li>
                <li><b>🤖 AI Ders Özetleme:</b> Ders içeriklerinin anında özetini tek tıkla çıkarma (Gemini & Groq).</li>
                <li><b>📝 Akıllı Ödev Değerlendirme:</b> Öğrencilerin yazdığı ödevleri/metinleri yapay zekayla anında değerlendirme ve geri bildirim.</li>
                <li><b>📈 Detaylı Notlandırma:</b> 100 üzerinden otomatik AI puanlaması.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        tab_login, tab_register = st.tabs(["Giriş Yap", "Kayıt Ol"])
        
        with tab_login:
            login_username = st.text_input("Kullanıcı Adı", key="login_username")
            login_password = st.text_input("Şifre", type="password", key="login_password")
            
            if st.button("Giriş Yap", key="btn_login"):
                if not is_connected:
                    st.error("API sunucusu çalışmıyor, giriş yapılamaz.")
                    return
                try:
                    res = requests.post(f"{API_BASE_URL}/login", json={
                        "username": login_username,
                        "password": login_password
                    })
                    if res.status_code == 200:
                        st.session_state.user = res.json()
                        st.success("Giriş başarılı!")
                        st.rerun()
                    else:
                        st.error(res.json().get("detail", "Giriş başarısız."))
                except Exception as e:
                    st.error(f"Bağlantı hatası: {str(e)}")
                    
        with tab_register:
            reg_username = st.text_input("Kullanıcı Adı", key="reg_username")
            reg_email = st.text_input("E-posta Adresi", key="reg_email")
            reg_password = st.text_input("Şifre", type="password", key="reg_password")
            reg_role = st.selectbox("Rol", ["Öğrenci", "Eğitmen"], key="reg_role")
            
            if st.button("Kayıt Ol", key="btn_register"):
                if not is_connected:
                    st.error("API sunucusu çalışmıyor, kayıt yapılamaz.")
                    return
                role_val = "student" if reg_role == "Öğrenci" else "teacher"
                try:
                    res = requests.post(f"{API_BASE_URL}/register", json={
                        "username": reg_username,
                        "email": reg_email,
                        "password": reg_password,
                        "role": role_val
                    })
                    if res.status_code == 201:
                        st.success("Kayıt başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.")
                    else:
                        st.error(res.json().get("detail", "Kayıt başarısız."))
                except Exception as e:
                    st.error(f"Bağlantı hatası: {str(e)}")

# ==========================================
# Teacher Dashboard
# ==========================================
def render_teacher_dashboard():
    st.markdown(f"<h2>Eğitmen Kontrol Paneli: Hoş Geldiniz, {st.session_state.user['username']}</h2>", unsafe_allow_html=True)
    
    menu = st.tabs(["📚 Kurslarım & Ders Ekle", "📝 Ödev Değerlendirmeleri"])
    
    # Tab 1: Course and Lesson Management
    with menu[0]:
        col_list, col_add = st.columns([2, 1])
        
        with col_add:
            st.markdown("<div class='glass-card'><h4>Yeni Kurs Oluştur</h4>", unsafe_allow_html=True)
            c_title = st.text_input("Kurs Adı")
            c_desc = st.text_area("Kurs Açıklaması")
            if st.button("Kurs Oluştur"):
                if not c_title:
                    st.warning("Lütfen kurs adı girin.")
                else:
                    try:
                        res = requests.post(f"{API_BASE_URL}/courses", json={
                            "title": c_title,
                            "description": c_desc,
                            "teacher_id": st.session_state.user["id"]
                        })
                        if res.status_code == 201:
                            st.success(f"'{c_title}' kursu başarıyla oluşturuldu!")
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Kurs oluşturulamadı."))
                    except Exception as e:
                        st.error(f"Hata: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_list:
            st.markdown("### Mevcut Kurslarınız")
            try:
                courses = requests.get(f"{API_BASE_URL}/courses").json()
                # Filter teacher's own courses
                my_courses = [c for c in courses if c["teacher_id"] == st.session_state.user["id"]]
                
                if not my_courses:
                    st.info("Henüz bir kurs oluşturmadınız.")
                else:
                    for course in my_courses:
                        with st.expander(f"📖 {course['title']}"):
                            st.write(course["description"] or "Açıklama belirtilmemiş.")
                            
                            # Fetch lessons for this course
                            lessons_res = requests.get(f"{API_BASE_URL}/courses/{course['id']}/lessons")
                            lessons = lessons_res.json() if lessons_res.status_code == 200 else []
                            
                            st.markdown("**Mevcut Ders İçerikleri:**")
                            if not lessons:
                                st.write("Bu kursta henüz ders yok.")
                            else:
                                for idx, lesson in enumerate(lessons):
                                    st.markdown(f"**{idx+1}. {lesson['title']}**")
                                    st.write(lesson["content"][:200] + "..." if len(lesson["content"]) > 200 else lesson["content"])
                                    
                                    # Summarize button & AI Summary displaying
                                    if lesson.get("summary"):
                                        st.info(f"💡 **AI Özeti:** {lesson['summary']}")
                                    else:
                                        if st.button(f"Yapay Zeka Özeti Oluştur ({lesson['title']})", key=f"sum_{lesson['id']}"):
                                            with st.spinner("AI Özeti oluşturuluyor..."):
                                                sum_res = requests.post(
                                                    f"{API_BASE_URL}/lessons/{lesson['id']}/summarize?provider={st.session_state.selected_provider}",
                                                    headers=get_headers()
                                                )
                                                if sum_res.status_code == 200:
                                                    st.success("Özet başarıyla oluşturuldu!")
                                                    st.rerun()
                                                else:
                                                    st.error("Özet oluşturulamadı. API Anahtarınızı kontrol edin.")
                                    st.divider()
                                    
                            # Form to add lesson
                            st.markdown("---")
                            st.markdown("**Bu Kursa Yeni Ders Ekle**")
                            l_title = st.text_input("Ders Başlığı", key=f"lti_{course['id']}")
                            l_content = st.text_area("Ders İçeriği (Konu Anlatımı)", key=f"lco_{course['id']}")
                            if st.button("Dersi Kaydet", key=f"lbtn_{course['id']}"):
                                if not l_title or not l_content:
                                    st.warning("Lütfen başlık ve içerik alanlarını doldurun.")
                                else:
                                    try:
                                        res = requests.post(f"{API_BASE_URL}/courses/{course['id']}/lessons", json={
                                            "title": l_title,
                                            "content": l_content
                                        })
                                        if res.status_code == 201:
                                            st.success("Ders başarıyla eklendi!")
                                            st.rerun()
                                        else:
                                            st.error("Ders eklenirken bir hata oluştu.")
                                    except Exception as e:
                                        st.error(f"Hata: {str(e)}")
            except Exception as e:
                st.error(f"Kurslar yüklenirken hata oluştu: {str(e)}")

    # Tab 2: Submissions review
    with menu[1]:
        st.markdown("### Öğrencilerden Gelen Ödevlerin AI Analiz Raporları")
        try:
            courses = requests.get(f"{API_BASE_URL}/courses").json()
            my_courses = [c for c in courses if c["teacher_id"] == st.session_state.user["id"]]
            
            if not my_courses:
                st.info("Görüntülenecek kursunuz bulunmuyor.")
            else:
                course_opts = {c["title"]: c["id"] for c in my_courses}
                sel_c_title = st.selectbox("Kurs Seçin", list(course_opts.keys()), key="teacher_sub_course")
                sel_c_id = course_opts[sel_c_title]
                
                lessons_res = requests.get(f"{API_BASE_URL}/courses/{sel_c_id}/lessons")
                lessons = lessons_res.json() if lessons_res.status_code == 200 else []
                
                if not lessons:
                    st.info("Bu kursta henüz bir ders yok.")
                else:
                    lesson_opts = {l["title"]: l["id"] for l in lessons}
                    sel_l_title = st.selectbox("Ders Seçin", list(lesson_opts.keys()), key="teacher_sub_lesson")
                    sel_l_id = lesson_opts[sel_l_title]
                    
                    sub_res = requests.get(f"{API_BASE_URL}/submissions/lesson/{sel_l_id}")
                    if sub_res.status_code == 200:
                        submissions = sub_res.json()
                        if not submissions:
                            st.info("Bu ders için henüz ödev teslim edilmemiş.")
                        else:
                            for idx, sub in enumerate(submissions):
                                grade = sub.get("grade", 0)
                                if grade >= 85:
                                    g_class = "grade-high"
                                elif grade >= 50:
                                    g_class = "grade-mid"
                                else:
                                    g_class = "grade-low"
                                    
                                # Fetch student details (mocking username placeholder/endpoint if needed,
                                # but we can query user by ID or display ID)
                                st.markdown(f"""
                                <div class='glass-card'>
                                    <h5>Öğrenci ID: {sub['student_id']} - Teslim #{sub['id']}</h5>
                                    <span class='grade-badge {g_class}'>Not: {grade} / 100</span>
                                    <p style='margin-top: 10px;'><b>Öğrenci Yanıtı:</b><br>{sub['student_text']}</p>
                                    <blockquote style='border-left: 3px solid #6366f1; padding-left: 10px; margin-left: 0; color: #a5b4fc;'>
                                        <b>🤖 AI Geri Bildirimi ({sub.get('provider_used', '').upper()}):</b><br>{sub['feedback']}
                                    </blockquote>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.error("Ödevler getirilemedi.")
        except Exception as e:
            st.error(f"Hata: {str(e)}")

# ==========================================
# Student Dashboard
# ==========================================
def render_student_dashboard():
    st.markdown(f"<h2>Öğrenci Kontrol Paneli: Hoş Geldiniz, {st.session_state.user['username']}</h2>", unsafe_allow_html=True)
    
    menu = st.tabs(["📖 Kurslar & Ders Çalış", "✍️ Ödevlerim & Değerlendirmeler"])
    
    # Tab 1: Study Materials
    with menu[0]:
        try:
            courses = requests.get(f"{API_BASE_URL}/courses").json()
            if not courses:
                st.info("Sistemde henüz kurs bulunmuyor.")
            else:
                course_opts = {c["title"]: c["id"] for c in courses}
                sel_c_title = st.selectbox("Çalışmak İstediğiniz Kursu Seçin", list(course_opts.keys()))
                sel_c_id = course_opts[sel_c_title]
                
                lessons_res = requests.get(f"{API_BASE_URL}/courses/{sel_c_id}/lessons")
                lessons = lessons_res.json() if lessons_res.status_code == 200 else []
                
                if not lessons:
                    st.info("Bu kursta henüz bir ders içeriği yüklenmemiş.")
                else:
                    lesson_opts = {l["title"]: l["id"] for l in lessons}
                    sel_l_title = st.selectbox("Ders Seçin", list(lesson_opts.keys()))
                    sel_l_id = lesson_opts[sel_l_title]
                    
                    selected_lesson = next(l for l in lessons if l["id"] == sel_l_id)
                    
                    # Display Lesson details
                    st.markdown(f"### 📖 {selected_lesson['title']}")
                    
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("##### Ders Konusu")
                    st.write(selected_lesson["content"])
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if selected_lesson.get("summary"):
                        st.markdown("<div class='glass-card' style='border-left: 4px solid #a855f7;'>", unsafe_allow_html=True)
                        st.markdown("##### 💡 Yapay Zeka Özeti")
                        st.write(selected_lesson["summary"])
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.info("Bu ders için eğitmen henüz yapay zeka özeti oluşturmamış.")
                    
                    # Submission Area
                    st.markdown("---")
                    st.markdown("#### ✍️ Ödevini Yapay Zeka ile Değerlendir")
                    st.write("Dersle ilgili edindiğiniz bilgileri açıklayın veya eğitmenin verdiği soruyu yanıtlayın. AI anında değerlendirip not verecektir.")
                    
                    student_text = st.text_area("Cevabınız / Analiziniz / Kompozisyonunuz", height=150, placeholder="Yazmaya başlayın...")
                    
                    if st.button("Ödevi Gönder ve AI Puanı Al"):
                        if not student_text.strip():
                            st.warning("Lütfen bir cevap metni girin.")
                        else:
                            with st.spinner("Yapay Zeka ödevinizi inceliyor, lütfen bekleyin..."):
                                try:
                                    res = requests.post(
                                        f"{API_BASE_URL}/lessons/{sel_l_id}/submissions",
                                        json={
                                            "student_id": st.session_state.user["id"],
                                            "student_text": student_text,
                                            "provider": st.session_state.selected_provider
                                        },
                                        headers=get_headers()
                                    )
                                    if res.status_code == 200:
                                        result = res.json()
                                        st.success("Ödeviniz başarıyla değerlendirildi!")
                                        
                                        grade = result.get("grade", 0)
                                        if grade >= 85:
                                            g_class = "grade-high"
                                        elif grade >= 50:
                                            g_class = "grade-mid"
                                        else:
                                            g_class = "grade-low"
                                            
                                        st.markdown(f"""
                                        <div class='glass-card' style='margin-top: 15px; border: 1px solid rgba(16, 185, 129, 0.3);'>
                                            <h4>Değerlendirme Sonucu</h4>
                                            <span class='grade-badge {g_class}'>Not: {grade} / 100</span>
                                            <p style='margin-top:15px;'><b>🤖 Geri Bildirim:</b><br>{result.get('feedback')}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.error("Değerlendirme işlemi başarısız oldu. API Anahtarınızı kontrol edin.")
                                except Exception as e:
                                    st.error(f"Hata: {str(e)}")
        except Exception as e:
            st.error(f"Hata: {str(e)}")

    # Tab 2: Historical submissions
    with menu[1]:
        st.markdown("### Önceki Ödevleriniz ve AI Notları")
        try:
            sub_res = requests.get(f"{API_BASE_URL}/submissions/student/{st.session_state.user['id']}")
            if sub_res.status_code == 200:
                submissions = sub_res.json()
                if not submissions:
                    st.info("Henüz ödev tesliminiz bulunmuyor.")
                else:
                    for sub in submissions:
                        grade = sub.get("grade", 0)
                        if grade >= 85:
                            g_class = "grade-high"
                        elif grade >= 50:
                            g_class = "grade-mid"
                        else:
                            g_class = "grade-low"
                            
                        # Get lesson info for title
                        try:
                            lesson_info = requests.get(f"{API_BASE_URL}/lessons/{sub['lesson_id']}").json()
                            l_title = lesson_info.get("title", f"Ders #{sub['lesson_id']}")
                        except Exception:
                            l_title = f"Ders #{sub['lesson_id']}"
                            
                        st.markdown(f"""
                        <div class='glass-card'>
                            <h4>📖 {l_title}</h4>
                            <span class='grade-badge {g_class}'>Not: {grade} / 100</span>
                            <p style='margin-top:10px;'><b>Cevabınız:</b> {sub['student_text']}</p>
                            <blockquote style='border-left: 3px solid #a855f7; padding-left: 10px; margin-left: 0; color: #d8b4fe;'>
                                <b>🤖 AI Geri Bildirimi ({sub.get('provider_used', '').upper()}):</b><br>{sub['feedback']}
                            </blockquote>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error("Ödevler yüklenemedi.")
        except Exception as e:
            st.error(f"Hata: {str(e)}")

# ==========================================
# Main Navigation Controller
# ==========================================
if st.session_state.user is None:
    render_auth_page()
else:
    if st.session_state.user["role"] == "teacher":
        render_teacher_dashboard()
    else:
        render_student_dashboard()
