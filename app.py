import streamlit as st
import requests
import os
import sys
import time
import threading
from dotenv import load_dotenv

# ==========================================
# Environment & Backend Startup
# ==========================================
load_dotenv()

# Module-level flag — ensures backend only starts ONCE per Python process,
# even when Streamlit reruns the script on every user interaction.
_BACKEND_STARTED = False

def _run_uvicorn():
    import uvicorn
    config = uvicorn.Config(
        "api:app", host="127.0.0.1", port=8000, log_level="error"
    )
    server = uvicorn.Server(config)
    # Disable OS signal handlers — only the main thread can register them.
    server.install_signal_handlers = lambda: None
    server.run()

def _ensure_backend():
    global _BACKEND_STARTED
    if _BACKEND_STARTED:
        return
    # Check if already running (e.g. launched externally)
    try:
        requests.get("http://127.0.0.1:8000/courses", timeout=0.3)
        _BACKEND_STARTED = True
        return
    except Exception:
        pass
    # Start in a background daemon thread
    _BACKEND_STARTED = True
    t = threading.Thread(target=_run_uvicorn, daemon=True)
    t.start()
    # Wait up to 4 seconds for the port to open
    for _ in range(8):
        time.sleep(0.5)
        try:
            requests.get("http://127.0.0.1:8000/courses", timeout=0.3)
            return
        except Exception:
            pass

_ensure_backend()


# ==========================================
# Page Configuration – no sidebar
# ==========================================
st.set_page_config(
    page_title="AI-LMS | Yapay Zeka Destekli Öğrenme Yönetim Sistemi",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
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
# Global CSS – hides sidebar & adds navbar
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    /* ── Remove sidebar & hamburger ─────── */
    [data-testid="stSidebar"]          { display: none !important; }
    [data-testid="collapsedControl"]   { display: none !important; }
    header[data-testid="stHeader"]     { display: none !important; }
    #MainMenu, footer                  { visibility: hidden; }

    /* ── Main Background ────────────────── */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e2246 0%, #0d1021 70%);
        color: #e2e8f0;
    }

    /* ── Sticky Top Navigation Bar ──────── */
    .lms-navbar {
        position: sticky;
        top: 0;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 2rem;
        height: 64px;
        background: rgba(13, 16, 33, 0.85);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border-bottom: 1px solid rgba(99, 102, 241, 0.25);
        box-shadow: 0 4px 32px rgba(0, 0, 0, 0.4);
        margin-bottom: 0;
    }

    .lms-navbar-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 1.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-decoration: none;
        white-space: nowrap;
    }

    .lms-navbar-right {
        display: flex;
        align-items: center;
        gap: 1.2rem;
    }

    .nav-status {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.8rem;
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        font-weight: 500;
    }
    .nav-status.online  { background: rgba(16,185,129,.15); color: #10b981; border: 1px solid rgba(16,185,129,.35); }
    .nav-status.offline { background: rgba(239,68,68,.15);  color: #ef4444; border: 1px solid rgba(239,68,68,.35); }

    .nav-provider {
        font-size: 0.8rem;
        padding: 0.3rem 0.9rem;
        border-radius: 999px;
        background: rgba(99,102,241,.15);
        color: #a5b4fc;
        border: 1px solid rgba(99,102,241,.35);
        font-weight: 500;
    }

    .nav-user {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        padding: 0.3rem 1rem;
        border-radius: 999px;
        background: rgba(168,85,247,.1);
        border: 1px solid rgba(168,85,247,.3);
        color: #d8b4fe;
        font-weight: 600;
    }

    /* ── Content Wrapper (adds top padding) */
    .page-content { padding-top: 1.5rem; }

    /* ── Premium Title ───────────────────── */
    .main-title {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        line-height: 1.15;
    }
    .subtitle { color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; }

    /* ── Glassmorphism Cards ─────────────── */
    .glass-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 30px rgba(0,0,0,0.25);
        backdrop-filter: blur(6px);
    }
    .course-card {
        background: linear-gradient(135deg,rgba(99,102,241,0.1) 0%,rgba(168,85,247,0.05) 100%);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: transform .2s, border-color .2s;
    }
    .course-card:hover { transform: translateY(-2px); border-color: rgba(99,102,241,0.45); }

    /* ── Grade Badges ────────────────────── */
    .grade-badge {
        display: inline-block;
        padding: .25rem .75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: .9rem;
    }
    .grade-high { background: rgba(16,185,129,.2); color:#10b981; border:1px solid rgba(16,185,129,.4); }
    .grade-mid  { background: rgba(245,158,11,.2);  color:#f59e0b; border:1px solid rgba(245,158,11,.4); }
    .grade-low  { background: rgba(239,68,68,.2);   color:#ef4444; border:1px solid rgba(239,68,68,.4); }

    /* ── Buttons ─────────────────────────── */
    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: .5rem 1.5rem;
        font-weight: 600;
        transition: opacity .2s, transform .15s;
    }
    div.stButton > button:hover { opacity: .88; transform: translateY(-1px); color: white; }

    /* ── Hero feature icons ──────────────── */
    .feature-item {
        display: flex;
        align-items: flex-start;
        gap: 0.9rem;
        padding: 1rem;
        border-radius: 12px;
        background: rgba(255,255,255,.03);
        border: 1px solid rgba(255,255,255,.06);
        margin-bottom: 0.75rem;
        transition: background .2s;
    }
    .feature-item:hover { background: rgba(99,102,241,.08); }
    .feature-icon {
        font-size: 1.6rem;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .feature-text h4 { margin: 0 0 .25rem; color: #c4b5fd; font-size: .95rem; }
    .feature-text p  { margin: 0; color: #94a3b8; font-size: .82rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# API Helper Functions
# ==========================================
def check_backend_status():
    try:
        requests.get(f"{API_BASE_URL}/courses", timeout=2)
        return True
    except Exception:
        return False

def get_headers():
    provider = st.session_state.selected_provider
    key = st.session_state.api_key_gemini if provider == "gemini" else st.session_state.api_key_groq
    return {"X-API-Key": key}

# ==========================================
# Inline Top Navigation Bar (rendered via HTML)
# ==========================================
is_connected = check_backend_status()
status_cls  = "online"  if is_connected else "offline"
status_dot  = "🟢 API Bağlı" if is_connected else "🔴 Çevrimdışı"

provider_label = f"🤖 {st.session_state.selected_provider.upper()}"

if st.session_state.user:
    user_label = f"👤 {st.session_state.user['username']} · {st.session_state.user['role'].upper()}"
else:
    user_label = "🔒 Giriş Yapılmadı"

st.markdown(f"""
<div class="lms-navbar">
    <span class="lms-navbar-brand">🎓 AI-LMS</span>
    <div class="lms-navbar-right">
        <span class="nav-status {status_cls}">{status_dot}</span>
        <span class="nav-provider">{provider_label}</span>
        <span class="nav-user">{user_label}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Provider selector + logout rendered as compact Streamlit widgets BELOW navbar
nav_col1, nav_col2, nav_col3 = st.columns([6, 2, 1])
with nav_col2:
    provider = st.selectbox(
        "AI Sağlayıcı",
        ["groq", "gemini"],
        index=0 if st.session_state.selected_provider == "groq" else 1,
        key="selected_provider_selectbox",
        label_visibility="collapsed"
    )
    st.session_state.selected_provider = provider
with nav_col3:
    if st.session_state.user:
        if st.button("Çıkış", use_container_width=True):
            st.session_state.user = None
            st.rerun()

st.divider()

# ==========================================
# Login / Register View
# ==========================================
def render_auth_page():
    st.markdown("<h1 class='main-title'>🎓 Yapay Zeka Destekli LMS</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Kurs Oluşturma · AI İçerik Özetleme · Akıllı Ödev Değerlendirme</p>", unsafe_allow_html=True)

    col_feat, col_auth = st.columns([1.1, 1])

    with col_feat:
        st.markdown("""
        <div class="feature-item">
            <span class="feature-icon">📚</span>
            <div class="feature-text">
                <h4>Kurs & Ders Yönetimi</h4>
                <p>Eğitmenler için kolay kurs müfredatı tasarımı ve ders içerikleri yönetimi.</p>
            </div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <div class="feature-text">
                <h4>AI Ders Özetleme</h4>
                <p>Ders içeriklerinin yapay zeka ile anında özetini tek tıkla oluşturun (Gemini & Groq).</p>
            </div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">✍️</span>
            <div class="feature-text">
                <h4>Akıllı Ödev Değerlendirme</h4>
                <p>Öğrenci ödevlerini yapay zekayla anında değerlendirin ve detaylı geri bildirim alın.</p>
            </div>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📈</span>
            <div class="feature-text">
                <h4>Otomatik Notlandırma</h4>
                <p>100 üzerinden AI destekli puanlama sistemi ile şeffaf ve tutarlı değerlendirme.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_auth:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])

        with tab_login:
            login_username = st.text_input("Kullanıcı Adı", key="login_username")
            login_password = st.text_input("Şifre", type="password", key="login_password")
            if st.button("Giriş Yap", key="btn_login", use_container_width=True):
                if not is_connected:
                    st.error("API sunucusu çalışmıyor, giriş yapılamaz.")
                    return
                try:
                    res = requests.post(f"{API_BASE_URL}/login", json={
                        "username": login_username, "password": login_password
                    })
                    if res.status_code == 200:
                        st.session_state.user = res.json()
                        st.success("Giriş başarılı!")
                        st.rerun()
                    else:
                        st.error(res.json().get("detail", "Giriş başarısız."))
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")

        with tab_register:
            reg_username = st.text_input("Kullanıcı Adı", key="reg_username")
            reg_email    = st.text_input("E-posta Adresi", key="reg_email")
            reg_password = st.text_input("Şifre", type="password", key="reg_password")
            reg_role     = st.selectbox("Rol", ["Öğrenci", "Eğitmen"], key="reg_role")
            if st.button("Kayıt Ol", key="btn_register", use_container_width=True):
                if not is_connected:
                    st.error("API sunucusu çalışmıyor.")
                    return
                role_val = "student" if reg_role == "Öğrenci" else "teacher"
                try:
                    res = requests.post(f"{API_BASE_URL}/register", json={
                        "username": reg_username, "email": reg_email,
                        "password": reg_password, "role": role_val
                    })
                    if res.status_code == 201:
                        st.success("Kayıt başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.")
                    else:
                        st.error(res.json().get("detail", "Kayıt başarısız."))
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# Teacher Dashboard
# ==========================================
def render_teacher_dashboard():
    st.markdown(f"<h2 style='margin-bottom:.25rem'>Hoş Geldiniz, <span style='color:#a855f7'>{st.session_state.user['username']}</span> 👨‍🏫</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;margin-bottom:1.5rem'>Eğitmen Kontrol Paneli</p>", unsafe_allow_html=True)

    tab_courses, tab_subs = st.tabs(["📚 Kurslarım & Ders Ekle", "📝 Ödev Değerlendirmeleri"])

    with tab_courses:
        col_list, col_add = st.columns([2, 1])

        with col_add:
            st.markdown("<div class='glass-card'><h4>➕ Yeni Kurs Oluştur</h4>", unsafe_allow_html=True)
            c_title = st.text_input("Kurs Adı", key="new_c_title")
            c_desc  = st.text_area("Kurs Açıklaması", key="new_c_desc")
            if st.button("Kurs Oluştur", key="btn_create_course", use_container_width=True):
                if not c_title:
                    st.warning("Lütfen kurs adı girin.")
                else:
                    try:
                        res = requests.post(f"{API_BASE_URL}/courses", json={
                            "title": c_title, "description": c_desc,
                            "teacher_id": st.session_state.user["id"]
                        })
                        if res.status_code == 201:
                            st.success(f"'{c_title}' kursu oluşturuldu!")
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Kurs oluşturulamadı."))
                    except Exception as e:
                        st.error(f"Hata: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_list:
            st.markdown("### Mevcut Kurslarınız")
            try:
                courses    = requests.get(f"{API_BASE_URL}/courses").json()
                my_courses = [c for c in courses if c["teacher_id"] == st.session_state.user["id"]]
                if not my_courses:
                    st.info("Henüz bir kurs oluşturmadınız.")
                else:
                    for course in my_courses:
                        with st.expander(f"📖 {course['title']}"):
                            st.write(course["description"] or "Açıklama belirtilmemiş.")
                            lessons_res = requests.get(f"{API_BASE_URL}/courses/{course['id']}/lessons")
                            lessons = lessons_res.json() if lessons_res.status_code == 200 else []

                            st.markdown("**Mevcut Dersler:**")
                            if not lessons:
                                st.write("Bu kursta henüz ders yok.")
                            else:
                                for idx, lesson in enumerate(lessons):
                                    st.markdown(f"**{idx+1}. {lesson['title']}**")
                                    st.write(lesson["content"][:200] + "…" if len(lesson["content"]) > 200 else lesson["content"])
                                    if lesson.get("summary"):
                                        st.info(f"💡 **AI Özeti:** {lesson['summary']}")
                                    else:
                                        if st.button(f"🤖 AI Özeti Oluştur ({lesson['title']})", key=f"sum_{lesson['id']}"):
                                            with st.spinner("Özet oluşturuluyor…"):
                                                sum_res = requests.post(
                                                    f"{API_BASE_URL}/lessons/{lesson['id']}/summarize?provider={st.session_state.selected_provider}",
                                                    headers=get_headers()
                                                )
                                                if sum_res.status_code == 200:
                                                    st.success("Özet oluşturuldu!")
                                                    st.rerun()
                                                else:
                                                    st.error("Özet oluşturulamadı.")
                                    st.divider()

                            st.markdown("**Bu Kursa Yeni Ders Ekle**")
                            l_title   = st.text_input("Ders Başlığı",  key=f"lti_{course['id']}")
                            l_content = st.text_area("Ders İçeriği",   key=f"lco_{course['id']}")
                            if st.button("Dersi Kaydet", key=f"lbtn_{course['id']}"):
                                if not l_title or not l_content:
                                    st.warning("Başlık ve içerik alanlarını doldurun.")
                                else:
                                    try:
                                        res = requests.post(f"{API_BASE_URL}/courses/{course['id']}/lessons",
                                                            json={"title": l_title, "content": l_content})
                                        if res.status_code == 201:
                                            st.success("Ders eklendi!")
                                            st.rerun()
                                        else:
                                            st.error("Ders eklenemedi.")
                                    except Exception as e:
                                        st.error(f"Hata: {e}")
            except Exception as e:
                st.error(f"Kurslar yüklenirken hata: {e}")

    with tab_subs:
        st.markdown("### Öğrencilerden Gelen Ödevlerin AI Analiz Raporları")
        try:
            courses    = requests.get(f"{API_BASE_URL}/courses").json()
            my_courses = [c for c in courses if c["teacher_id"] == st.session_state.user["id"]]
            if not my_courses:
                st.info("Görüntülenecek kursunuz yok.")
            else:
                course_opts  = {c["title"]: c["id"] for c in my_courses}
                sel_c_title  = st.selectbox("Kurs Seçin", list(course_opts.keys()), key="teacher_sub_course")
                sel_c_id     = course_opts[sel_c_title]
                lessons_res  = requests.get(f"{API_BASE_URL}/courses/{sel_c_id}/lessons")
                lessons      = lessons_res.json() if lessons_res.status_code == 200 else []
                if not lessons:
                    st.info("Bu kursta ders yok.")
                else:
                    lesson_opts = {l["title"]: l["id"] for l in lessons}
                    sel_l_title = st.selectbox("Ders Seçin", list(lesson_opts.keys()), key="teacher_sub_lesson")
                    sel_l_id    = lesson_opts[sel_l_title]
                    sub_res     = requests.get(f"{API_BASE_URL}/submissions/lesson/{sel_l_id}")
                    if sub_res.status_code == 200:
                        submissions = sub_res.json()
                        if not submissions:
                            st.info("Bu ders için henüz ödev teslim edilmemiş.")
                        else:
                            for sub in submissions:
                                grade   = sub.get("grade", 0)
                                g_class = "grade-high" if grade >= 85 else ("grade-mid" if grade >= 50 else "grade-low")
                                st.markdown(f"""
                                <div class='glass-card'>
                                    <h5>Öğrenci ID: {sub['student_id']} — Teslim #{sub['id']}</h5>
                                    <span class='grade-badge {g_class}'>Not: {grade} / 100</span>
                                    <p style='margin-top:10px'><b>Öğrenci Yanıtı:</b><br>{sub['student_text']}</p>
                                    <blockquote style='border-left:3px solid #6366f1;padding-left:10px;margin-left:0;color:#a5b4fc'>
                                        <b>🤖 AI Geri Bildirimi ({sub.get('provider_used','').upper()}):</b><br>{sub['feedback']}
                                    </blockquote>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.error("Ödevler getirilemedi.")
        except Exception as e:
            st.error(f"Hata: {e}")

# ==========================================
# Student Dashboard
# ==========================================
def render_student_dashboard():
    st.markdown(f"<h2 style='margin-bottom:.25rem'>Hoş Geldiniz, <span style='color:#a855f7'>{st.session_state.user['username']}</span> 🎒</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;margin-bottom:1.5rem'>Öğrenci Kontrol Paneli</p>", unsafe_allow_html=True)

    tab_study, tab_history = st.tabs(["📖 Kurslar & Ders Çalış", "✍️ Ödevlerim & Değerlendirmeler"])

    with tab_study:
        try:
            courses = requests.get(f"{API_BASE_URL}/courses").json()
            if not courses:
                st.info("Sistemde henüz kurs bulunmuyor.")
            else:
                course_opts = {c["title"]: c["id"] for c in courses}
                sel_c_title = st.selectbox("Çalışmak İstediğiniz Kursu Seçin", list(course_opts.keys()))
                sel_c_id    = course_opts[sel_c_title]
                lessons_res = requests.get(f"{API_BASE_URL}/courses/{sel_c_id}/lessons")
                lessons     = lessons_res.json() if lessons_res.status_code == 200 else []
                if not lessons:
                    st.info("Bu kursta henüz ders içeriği yüklenmemiş.")
                else:
                    lesson_opts    = {l["title"]: l["id"] for l in lessons}
                    sel_l_title    = st.selectbox("Ders Seçin", list(lesson_opts.keys()))
                    sel_l_id       = lesson_opts[sel_l_title]
                    selected_lesson = next(l for l in lessons if l["id"] == sel_l_id)

                    st.markdown(f"### 📖 {selected_lesson['title']}")
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("##### Ders Konusu")
                    st.write(selected_lesson["content"])
                    st.markdown("</div>", unsafe_allow_html=True)

                    if selected_lesson.get("summary"):
                        st.markdown("<div class='glass-card' style='border-left:4px solid #a855f7'>", unsafe_allow_html=True)
                        st.markdown("##### 💡 Yapay Zeka Özeti")
                        st.write(selected_lesson["summary"])
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.info("Eğitmen henüz bu ders için AI özeti oluşturmamış.")

                    st.markdown("---")
                    st.markdown("#### ✍️ Ödevini Yapay Zeka ile Değerlendir")
                    st.write("Dersle ilgili edindiğin bilgileri açıkla. AI anında değerlendirip not verecek.")
                    student_text = st.text_area("Cevabınız / Analiziniz", height=150, placeholder="Yazmaya başlayın…")

                    if st.button("Ödevi Gönder ve AI Puanı Al", use_container_width=True):
                        if not student_text.strip():
                            st.warning("Lütfen bir cevap metni girin.")
                        else:
                            with st.spinner("Yapay Zeka ödevinizi inceliyor…"):
                                try:
                                    res = requests.post(
                                        f"{API_BASE_URL}/lessons/{sel_l_id}/submissions",
                                        json={"student_id": st.session_state.user["id"],
                                              "student_text": student_text,
                                              "provider": st.session_state.selected_provider},
                                        headers=get_headers()
                                    )
                                    if res.status_code == 200:
                                        result  = res.json()
                                        grade   = result.get("grade", 0)
                                        g_class = "grade-high" if grade >= 85 else ("grade-mid" if grade >= 50 else "grade-low")
                                        st.success("Ödeviniz değerlendirildi!")
                                        st.markdown(f"""
                                        <div class='glass-card' style='border:1px solid rgba(16,185,129,.3)'>
                                            <h4>Değerlendirme Sonucu</h4>
                                            <span class='grade-badge {g_class}'>Not: {grade} / 100</span>
                                            <p style='margin-top:15px'><b>🤖 Geri Bildirim:</b><br>{result.get('feedback')}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.error("Değerlendirme başarısız. API Anahtarınızı kontrol edin.")
                                except Exception as e:
                                    st.error(f"Hata: {e}")
        except Exception as e:
            st.error(f"Hata: {e}")

    with tab_history:
        st.markdown("### Önceki Ödevleriniz ve AI Notları")
        try:
            sub_res = requests.get(f"{API_BASE_URL}/submissions/student/{st.session_state.user['id']}")
            if sub_res.status_code == 200:
                submissions = sub_res.json()
                if not submissions:
                    st.info("Henüz ödev tesliminiz bulunmuyor.")
                else:
                    for sub in submissions:
                        grade   = sub.get("grade", 0)
                        g_class = "grade-high" if grade >= 85 else ("grade-mid" if grade >= 50 else "grade-low")
                        try:
                            lesson_info = requests.get(f"{API_BASE_URL}/lessons/{sub['lesson_id']}").json()
                            l_title = lesson_info.get("title", f"Ders #{sub['lesson_id']}")
                        except Exception:
                            l_title = f"Ders #{sub['lesson_id']}"
                        st.markdown(f"""
                        <div class='glass-card'>
                            <h4>📖 {l_title}</h4>
                            <span class='grade-badge {g_class}'>Not: {grade} / 100</span>
                            <p style='margin-top:10px'><b>Cevabınız:</b> {sub['student_text']}</p>
                            <blockquote style='border-left:3px solid #a855f7;padding-left:10px;margin-left:0;color:#d8b4fe'>
                                <b>🤖 AI Geri Bildirimi ({sub.get('provider_used','').upper()}):</b><br>{sub['feedback']}
                            </blockquote>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error("Ödevler yüklenemedi.")
        except Exception as e:
            st.error(f"Hata: {e}")

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
