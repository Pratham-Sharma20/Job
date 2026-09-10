# Early-Career Job Board & Automated Aggregator

A full-stack, automated early-career job intelligence platform that continuously tracks, aggregates, deduplicates, and alerts on software engineering internships, new grad opportunities, and SDE-I openings across top tech companies (FAANG, tier-1 tech firms, and high-growth startups).

---

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Project Directory Structure](#project-directory-structure)
- [Tech Stack](#tech-stack)
- [Data Flow & Scraping Pipeline](#data-flow--scraping-pipeline)
- [Database Schema (MongoDB)](#database-schema-mongodb)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [API Reference](#api-reference)
- [Running Scrapers](#running-scrapers)
- [Production Deployment](#production-deployment)

---

## Overview

Finding internships and early-career software roles across dozens of corporate portals is tedious and fragmented. Many top companies (such as Apple, Google, Microsoft, and Workday tenants) use JavaScript-heavy Single Page Application (SPA) career portals or private internal APIs that aren't indexed on standard job boards.

This project solves that by:
1. Running automated scrapers using headless browsers (**Playwright**) and targeted API reverse-engineering.
2. Storing and deduplicating jobs inside **MongoDB Atlas**.
3. Sending instant **Telegram alerts** as soon as a new job is discovered.
4. Serving a clean **REST API** using **Flask**.
5. Displaying listings via a responsive **React 19 + Vite** frontend with live company filtering, keyword search, and pagination.

---

## Key Features

- **Multi-Source Scraping Pipeline**:
  - **Direct APIs**: Amazon Jobs API, Greenhouse boards, Lever postings, Workday CXS endpoints.
  - **Reverse-Engineered Internal APIs**: Microsoft Careers PCSX search API with automatic pagination and rate-limit backoff.
  - **Headless Browser Automation (Playwright)**: Google Careers (crawling dynamic SPAs and handling next-page pagination) and Apple Jobs.
  - **Embedded JSON Parsing**: Adobe Careers Phenom platform (`phApp.ddo` state extraction).
- **Targeted Early-Career Filtering**: Automated keyword matching for interns, graduates, entry-level, and SDE-I, with exclusion filters for senior/staff/director roles.
- **Real-Time Push Alerts**: Telegram bot notifications dispatch markdown-formatted messages with company, role, location, and apply links immediately upon discovering new jobs.
- **Idempotent Data Ingestion**: Uses unique job identifiers and URLs with MongoDB upsert operations to avoid duplicates.
- **Automated Scheduling**: Background scheduler thread running scheduled scraping jobs daily at 07:00.
- **Fast, Responsive Frontend**:
  - Warm, clean aesthetic with responsive multi-column layouts.
  - Live client-side search across role title, company, location, and source.
  - Multi-select company filter sidebar.
  - Pagination (12 jobs per page) with auto-reset on search/filter changes.

---

## System Architecture

```
                       ┌────────────────────────────────────────┐
                       │           Daily Scheduler              │
                       │           (scheduler.py)               │
                       └───────────────────┬────────────────────┘
                                           │ (Subprocess execution)
        ┌──────────────────┬───────────────┴───────────────┬──────────────────┐
        ▼                  ▼                               ▼                  ▼
┌───────────────┐  ┌───────────────┐               ┌───────────────┐  ┌───────────────┐
│   Amazon &    │  │   Microsoft   │               │ Google Search │  │ Adobe & Apple │
│  Greenhouse/  │  │  Careers API  │               │  (Playwright) │  │  (Playwright/ │
│ Lever/Workday │  │    (ms.py)    │               │  (google.py)  │  │ JSON parsing) │
│   (test.py)   │  └───────┬───────┘               └───────┬───────┘  └───────┬───────┘
└───────┬───────┘          │                               │                  │
        │                  │                               │                  │
        └──────────────────┼───────────────────────────────┴──────────────────┘
                           ▼
               ┌───────────────────────┐
               │    MongoDB Atlas      │◄─────── Flask REST API (app.py)
               │ (job_scraper_db.jobs) │                  ▲
               └───────────┬───────────┘                  │ (HTTP GET /jobs)
                           │                              │
         (On new job)      ▼                              │
               ┌───────────────────────┐          ┌───────┴───────┐
               │  Telegram Bot Alert   │          │  React + Vite │
               │     (notifier.py)     │          │   Frontend    │
               └───────────────────────┘          └───────────────┘
```

---

## Project Directory Structure

```
.
├── backend/
│   ├── app.py                 # Flask application entry point & REST API routes
│   ├── db.py                  # MongoDB Atlas connection setup
│   ├── notifier.py            # Telegram Bot notification sender
│   ├── scheduler.py           # Background cron-style scheduler (schedule library)
│   ├── test.py                # Scraper for Amazon, Greenhouse, Lever, Workday & FAANG search links
│   ├── ms.py                  # Dedicated Microsoft Careers API scraper & normalizer
│   ├── google.py              # Playwright-based scraper for Google Careers
│   ├── custom_scrape.py       # Scrapers for Adobe Careers and Apple Jobs
│   ├── requirements.txt       # Python dependencies list
│   ├── .env                   # Backend environment configuration (MongoDB, Telegram)
│   ├── career_jobs.csv        # Exported snapshot of scraped jobs
│   └── [dev-tools]            # Research & inspection scripts (dump_network.py, get_api.py, screenshot.py)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Hero/          # Header banner & search bar component
│   │   │   ├── JobCard/       # Individual job card displaying role, company, location & link
│   │   │   ├── JobList/       # Grid container rendering JobCards or loading/empty states
│   │   │   ├── Pagination/    # Page navigation controls (Previous, Next, Page X of Y)
│   │   │   └── Sidebar/       # Brand logo and company checkbox filter list
│   │   ├── App.jsx            # State management, data fetching, filtering & pagination logic
│   │   ├── App.css            # Root layout styling
│   │   ├── index.css          # Design tokens, variables & typography
│   │   └── main.jsx           # React DOM root render
│   ├── index.html             # HTML entry point
│   ├── package.json           # Node dependencies & npm scripts
│   ├── vite.config.js         # Vite configuration with @vitejs/plugin-react
│   └── .env                   # Frontend environment configuration (VITE_BACKEND_URL)
│
└── README.md                  # Project documentation
```

---

## Tech Stack

### Backend
- **Language**: Python 3.10+
- **Web Framework**: Flask 3.1, Flask-CORS
- **Database**: MongoDB Atlas (PyMongo 4.17)
- **Web Scraping & Automation**: Playwright, BeautifulSoup4, Requests, urllib3
- **Data Processing**: Pandas
- **Scheduling**: Schedule
- **Notifications**: Telegram Bot API

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite 8
- **Linter**: Oxlint
- **Styling**: Vanilla CSS3 (Custom design system, CSS Grid, Flexbox)

---

## Data Flow & Scraping Pipeline

1. **Trigger**:
   - Automated via `scheduler.py` at `07:00` daily.
   - Or triggered manually by running any individual scraper script.
2. **Scraping & Extraction**:
   - Scrapers extract `title`, `company`, `location`, `apply_link`, `posted_date`, and job descriptions.
   - Heuristics filter for early-career tags (`intern`, `new grad`, `graduate`, `fresher`, `entry level`, `sde i`) while discarding senior titles (`senior`, `principal`, `lead`, `manager`, `architect`).
3. **Database Upsert**:
   - Jobs are written to MongoDB using `jobs_collection.update_one({"company": ..., "job_id": ...}, {"$set": ...}, upsert=True)`.
   - Idempotency ensures existing jobs are updated without duplicates.
4. **Alert Notification**:
   - If an insert occurs (`upserted_id` is present), `notifier.send_telegram_notification()` dispatches a Markdown alert to the configured Telegram chat.
5. **Client Presentation**:
   - The React client fetches `GET /jobs` from the Flask backend.
   - The user can filter by company, search across any field, and paginate through results.

---

## Database Schema (MongoDB)

Documents in the `jobs` collection of `job_scraper_db` adhere to the following schema:

| Field | Type | Description |
|---|---|---|
| `job_id` | String | Unique job identifier (or canonical apply URL) |
| `company` | String | Employer name (e.g. `Microsoft`, `Google`, `Amazon`, `Adobe`) |
| `title` | String | Role title |
| `location` | String | City, state, or country |
| `apply_link` | String | Direct URL to the job posting or application page |
| `posted_date` | String | Date or timestamp the position was opened |
| `work_site` | String | Work arrangement (`On-site`, `Hybrid`, `Remote`) |
| `profession` | String | Category / department |
| `discipline` | String | Discipline (e.g. `Engineering and Product`) |
| `employment_type` | String | `Internship`, `Full time`, etc. |
| `description` | String | Summary or snippet of the role requirements |
| `source` | String | Portal or mechanism used (`Greenhouse`, `Microsoft Careers`, `Google Careers`, etc.) |
| `scraped_at` | String | ISO 8601 timestamp of scraping |

---

## Environment Variables

### Backend (`backend/.env`)
```env
# MongoDB Atlas connection string
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?appName=JOB

# Telegram Bot configuration for live notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Optional: Port for Flask server (defaults to 5000)
PORT=5000
```

### Frontend (`frontend/.env`)
```env
# Backend API URL (Local or deployed Render URL)
VITE_BACKEND_URL=http://localhost:5000
```

---

## Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **MongoDB Atlas** database account or local MongoDB instance
- **Playwright browsers** installed (`playwright install chromium`)

---

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. Create and configure your `backend/.env` file with `MONGO_URI`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID`.

5. Start the backend API server:
   ```bash
   python app.py
   ```
   The server starts at `http://localhost:5000` with the scheduler running in the background.

---

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Configure your `frontend/.env` file:
   ```bash
   VITE_BACKEND_URL=http://localhost:5000
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```

5. Open your browser at `http://localhost:5173` to explore the job board.

---

## API Reference

### 1. Health Check
- **Endpoint**: `GET /`
- **Response**:
  ```json
  {
    "message": "Job scraper backend is running"
  }
  ```

### 2. Get All Jobs
- **Endpoint**: `GET /jobs`
- **Response**: Array of job objects
  ```json
  [
    {
      "company": "Amazon",
      "title": "Software Development Engineer Intern",
      "location": "Bangalore, IND",
      "apply_link": "https://www.amazon.jobs/en/jobs/...",
      "source": "Amazon API",
      "scraped_at": "2026-09-10T07:00:00"
    }
  ]
  ```

---

## Running Scrapers Manually

Any scraper can be executed independently at any time:

```bash
cd backend

# Scrape Amazon, Greenhouse, Lever, Workday & FAANG search pages
python test.py

# Scrape Microsoft Careers API
python ms.py

# Scrape Google Careers (Headless browser)
python google.py

# Scrape Adobe and Apple Careers
python custom_scrape.py
```

---

## Production Deployment

- **Backend**: Hosted on [Render](https://render.com) using `gunicorn` as the WSGI server:
  - Start Command: `gunicorn app:app`
  - Environment variables set in Render dashboard (`MONGO_URI`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
- **Frontend**: Can be deployed to Vercel, Netlify, or Render Static Sites:
  - Build Command: `npm run build`
  - Publish Directory: `dist`
  - Environment variable: `VITE_BACKEND_URL=https://<your-backend-service>.onrender.com`
