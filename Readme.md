---
title: "ATS Resume Builder"
emoji: "📄"
colorFrom: "blue"
colorTo: "purple"
sdk: "docker"
sdk_version: "1.0"
app_port: 7860
pinned: false
---

# 🚀 ATS Resume Builder – Complete Job Search Platform

[![Hugging Face Spaces](https://img.shields.io/badge/🤗-Spaces-blue)](https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.2-black)](https://flask.palletsprojects.com/)

> **One‑stop platform to build ATS‑friendly resumes, track job applications, generate AI cover letters, practice with mock interviews, and learn from resume examples & interview videos.**

---

## 📌 Table of Contents

1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [Demo & Screenshots](#-demo--screenshots)
4. [Technology Stack](#-technology-stack)
5. [Installation & Local Setup](#-installation--local-setup)
6. [Environment Variables](#-environment-variables)
7. [API Endpoints](#-api-endpoints)
8. [Database Structure](#-database-structure)
9. [Deployment on Hugging Face Spaces](#-deployment-on-hugging-face-spaces)
10. [Troubleshooting & FAQ](#-troubleshooting--faq)
11. [Roadmap & Upcoming Features](#-roadmap--upcoming-features)
12. [Contributing](#-contributing)
13. [License](#-license)
14. [Acknowledgments](#-acknowledgments)

---

## 🌟 Overview

The **ATS Resume Builder** is a full‑stack web application that helps job seekers create optimized, machine‑readable resumes that pass Applicant Tracking Systems (ATS). It goes far beyond a simple form – it includes:

- **Interactive Resume Builder** with live preview, multiple templates, and voice‑to‑text input.
- **Resume Gallery** with 100+ industry‑specific examples (filterable by role).
- **Job Application Tracker** – Kanban‑style board to manage your job search.
- **AI Cover Letter Generator** – personalized cover letters using your resume data and job details.
- **Interview Preparation Hub** – embedded YouTube videos + search (coming: full mock interview system).
- **User Authentication** – secure signup/login with session management.
- **Admin‑like features** – add/edit/delete resume examples (via API).

This project is designed to be **deployed easily on Hugging Face Spaces** (using Docker) or any other PaaS (Render, Heroku, Railway).

---

## ✨ Key Features

### 🔹 Resume Builder
- **Dynamic sections** – add/remove work experiences, education, projects, and skills (as tags).
- **Live preview** – updates in real time as you type.
- **Template switching** – Classic, Modern, Student, Developer layouts.
- **Voice input** – use your microphone to fill any field (speech‑to‑text).
- **ATS score calculator** – instant feedback on how ATS‑friendly your resume is.
- **Import from profile** – pre‑fill personal details from your account.
- **Print / PDF** – print‑friendly view (hides UI elements).

### 🔹 My Resumes
- List all your saved resumes with title, ATS score, and download count.
- Edit, delete, or download each resume.
- Search and sort by date, name, or score.

### 🔹 Job Application Tracker
- Full CRUD for job applications.
- Fields: job title, company, location, status (Applied / Interview / Offer / Rejected), date applied, linked resume, notes.
- Color‑coded status badges.
- Link each application to a specific saved resume version.

### 🔹 AI Cover Letter Generator
- One‑click generation from any application card.
- Uses the job title, company, and your linked resume (or profile data).
- Returns a professional, ready‑to‑send cover letter.
- Copy to clipboard or save directly as a note in the application.

### 🔹 Resume Gallery & Interview Prep
- **Dynamic resume examples** – stored in the backend, filterable by industry (Software Engineering, Data Science, Marketing, Finance, Design, Sales).
- **Sample data seeding** – one‑click button to populate the gallery.
- **YouTube interview videos** – curated list of popular career advice videos (Tell Me About Yourself, STAR Method, Salary Negotiation, etc.).
- **Search YouTube** – type any keyword (e.g., “behavioral interview”) and see live results (requires YouTube API key).
- **Resume formatting tips** – a checklist of best practices.

### 🔹 User System
- Secure registration and login with bcrypt password hashing.
- Session‑based authentication (cookie).
- Profile page to update personal info, skills, summary, LinkedIn, GitHub, and profile image (base64).
- Profile strength indicator.

### 🔹 Admin / Content Management (via API)
- POST `/api/resources/resume-examples` – add new resume examples (must be logged in).
- DELETE `/api/resources/resume-examples/<id>` – remove an example.
- GET `/api/resources/resume-examples` – public endpoint to fetch all examples.

### 🔹 AI Assistant Chatbot (optional)
- Floating chatbot widget on dashboard and builder.
- Remembers conversation history (localStorage).
- Voice input and conversation export as .txt.

---

## 🖼️ Demo & Screenshots

> *(Add screenshots of your dashboard, builder, applications page, and gallery here.)*

![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+Screenshot)
![Resume Builder](https://via.placeholder.com/800x400?text=Builder+Screenshot)
![Job Applications](https://via.placeholder.com/800x400?text=Applications+Screenshot)
![Resume Gallery](https://via.placeholder.com/800x400?text=Gallery+Screenshot)

---

## 🛠️ Technology Stack

| Layer       | Technologies                                                                 |
|-------------|------------------------------------------------------------------------------|
| **Backend** | Flask 2.3.2, Flask-Cors, Flask-Session, bcrypt, python-dotenv, gunicorn      |
| **Frontend**| HTML5, CSS3, JavaScript (vanilla), Font Awesome, Google Fonts                |
| **Database**| JSON file (`database.json`) – *soon to be replaced with PostgreSQL*          |
| **AI / APIs**| OpenRouter (GPT‑4o‑mini) for cover letters & chat; YouTube Data API v3      |
| **Deployment**| Docker, Hugging Face Spaces (or Render, Heroku, Railway)                    |
| **Authentication**| Session‑based (cookie)                                                   |
| **Voice**  | Web Speech API (SpeechRecognition)                                          |

---

## 💻 Installation & Local Setup

### Prerequisites
- Python 3.11 or higher
- pip
- (Optional) Git

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ats-resume-builder.git
   cd ats-resume-builder