import streamlit as st
import json
import os
import time
import random
from datetime import datetime

# ----------------------------------
# PDF SUPPORT
# ----------------------------------
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

# ----------------------------------
# CONFIG
# ----------------------------------
st.set_page_config(
    page_title="LecturAI - Offline Video Analyzer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "local_db.json"
VIDEO_DIR = "saved_videos"

os.makedirs(VIDEO_DIR, exist_ok=True)

# ----------------------------------
# DATABASE FUNCTIONS
# ----------------------------------
def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def format_bytes(size):
    for unit in ["B","KB","MB","GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

def delete_lecture(lecture_id):
    db = load_db()
    new_db = []
    for l in db:
        if l["id"] != lecture_id:
            new_db.append(l)
        else:
            if os.path.exists(l["file_path"]):
                os.remove(l["file_path"])
    save_db(new_db)
    st.session_state.db = new_db
    st.session_state.view = "dashboard"
    st.rerun()

# ----------------------------------
# MOCK AI (DYNAMIC PER VIDEO)
# ----------------------------------
def generate_mock_notes(video_name):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    topics_pool = [
        "System Stability",
        "Control System Basics",
        "Signal Flow Graph",
        "Transfer Function",
        "Feedback Mechanism",
        "Frequency Response",
        "Time Domain Analysis"
    ]

    questions_pool = [
        "Define transfer function and explain its significance.",
        "Explain closed loop control system with example.",
        "Differentiate open loop and closed loop systems.",
        "What are poles and zeros? Explain their effect.",
        "Explain stability criteria in control systems."
    ]

    random.shuffle(topics_pool)
    random.shuffle(questions_pool)

    return {
        "id": f"lec_{int(time.time()*1000)}",
        "title": video_name,
        "date": timestamp,
        "summary": f"This offline AI-generated summary is created specifically for the video '{video_name}' on {timestamp}.",
        "important_topics": topics_pool[:4],
        "exam_questions": questions_pool[:4],
        "segments": [
            {
                "displayTime": "00:20",
                "title": f"Introduction to {video_name}",
                "content": [
                    "Overview of the lecture",
                    "Importance of the subject"
                ]
            },
            {
                "displayTime": "01:30",
                "title": "Core Concepts",
                "content": [
                    "Basic system definition",
                    "Real-world applications"
                ]
            },
            {
                "displayTime": "03:10",
                "title": "Exam Focus",
                "content": [
                    "Frequently asked theory",
                    "Common mistakes in exams"
                ]
            }
        ]
    }

# ----------------------------------
# PDF GENERATION
# ----------------------------------
def create_pdf(lecture):
    if not HAS_FPDF:
        return None

    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 10)
            self.cell(0, 10, "LecturAI Generated Notes", ln=True, align="R")

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 15)

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, lecture["title"], ln=True, align="C")

    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 8, f"Date: {lecture['date']}", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Executive Summary", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7, lecture["summary"])
    pdf.ln(4)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Important Topics", ln=True)
    pdf.set_font("Arial", "", 11)
    for t in lecture["important_topics"]:
        pdf.multi_cell(0, 6, f"- {t}")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Exam-Oriented Questions", ln=True)
    pdf.set_font("Arial", "", 11)
    for q in lecture["exam_questions"]:
        pdf.multi_cell(0, 6, f"- {q}")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Detailed Notes", ln=True)
    pdf.ln(3)

    for seg in lecture["segments"]:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"[{seg['displayTime']}] {seg['title']}", ln=True)
        pdf.set_font("Arial", "", 11)
        for c in seg["content"]:
            pdf.multi_cell(0, 6, f"- {c}")
        pdf.ln(2)

    return pdf.output(dest="S").encode("latin-1", "replace")

# ----------------------------------
# VIEWS
# ----------------------------------
def view_dashboard():
    st.title("📊 Dashboard")
    st.metric("Lectures Stored", len(st.session_state.db))

    if st.button("📤 Upload New Video"):
        st.session_state.view = "upload"
        st.rerun()

    for lec in st.session_state.db:
        with st.container(border=True):
            c1, c2 = st.columns([4,1])
            c1.write(lec["title"])
            if c2.button("Open", key=lec["id"]):
                st.session_state.active_lecture_id = lec["id"]
                st.session_state.view = "notes"
                st.rerun()

def view_upload():
    st.title("📤 Upload Video")
    video = st.file_uploader("Upload video file", type=["mp4","avi","mov"])

    if video and st.button("Process Video"):
        path = os.path.join(VIDEO_DIR, video.name)
        with open(path, "wb") as f:
            f.write(video.getbuffer())

        lecture = generate_mock_notes(video.name)
        lecture["file_path"] = path
        lecture["file_size"] = format_bytes(video.size)

        db = load_db()
        db.insert(0, lecture)
        save_db(db)

        st.session_state.db = db
        st.session_state.active_lecture_id = lecture["id"]
        st.session_state.view = "notes"
        st.rerun()

def view_notes():
    lec = next(l for l in st.session_state.db if l["id"] == st.session_state.active_lecture_id)

    st.title(lec["title"])
    st.video(lec["file_path"])
    st.info(lec["summary"])

    st.subheader("📌 Important Topics")
    for t in lec["important_topics"]:
        st.markdown(f"- {t}")

    st.subheader("❓ Exam-Oriented Questions")
    for q in lec["exam_questions"]:
        st.markdown(f"- {q}")

    if HAS_FPDF:
        pdf = create_pdf(lec)
        st.download_button(
            "📄 Download Notes as PDF",
            pdf,
            file_name=f"{lec['id']}_{lec['title'].replace(' ','_')}.pdf",
            mime="application/pdf",
            key=f"pdf_{lec['id']}"
        )

    if st.button("⬅ Back"):
        st.session_state.view = "dashboard"
        st.rerun()

def view_storage():
    st.title("💾 Storage Manager")
    for lec in st.session_state.db:
        c1, c2 = st.columns([4,1])
        c1.write(lec["title"])
        if c2.button("Delete", key="del_"+lec["id"]):
            delete_lecture(lec["id"])

# ----------------------------------
# MAIN
# ----------------------------------
def main():
    if "db" not in st.session_state:
        st.session_state.db = load_db()
    if "view" not in st.session_state:
        st.session_state.view = "dashboard"

    with st.sidebar:
        if st.button("Dashboard"):
            st.session_state.view = "dashboard"
        if st.button("Upload"):
            st.session_state.view = "upload"
        if st.button("Storage"):
            st.session_state.view = "storage"

    if st.session_state.view == "dashboard":
        view_dashboard()
    elif st.session_state.view == "upload":
        view_upload()
    elif st.session_state.view == "notes":
        view_notes()
    elif st.session_state.view == "storage":
        view_storage()

if __name__ == "__main__":
    main()