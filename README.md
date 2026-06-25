# AI Ad Creative Studio Pro 🚀

A premium SaaS-grade AI marketing platform designed to synthesize high-converting ad copy, hooks, primary texts, CTAs, video screenplays, and policy compliance reports. The system targets specific platforms (like Meta Ads) using the Google Gemini API (via LangChain), supports dynamic target audience ad set segmentation, and saves campaign records to Supabase Cloud PostgreSQL.

---

## 🎨 Key Features

* **SaaS-Grade Dashboard**: Two-column layout with input configurations on the left and beautifully formatted campaign outputs on the right.
* **Dual Theme Engine**: Complete UI personalization supporting a rich glassmorphism **Dark Theme** and an elevated paper-style **Light Theme**.
* **Meta Ad Sets**: Option to auto-generate or manually configure location, age, and interest groups for distinct target audience variations.
* **Asset Outputs**: Generates tailored hook variation cards, aligned headlines, primary copies (body copy), Call to Action configurations, and comprehensive video script framing boards.
* **Compliance screening**: Filters copies through custom Meta ad policy compliance parameters (Safe / Warning / High Risk) with actionable suggestions for safer rewrites.
* **Campaign History**: Interactive cards in the sidebar displaying past campaigns stored on Supabase Cloud, enabling instant loading or deletion.
* **Multi-Format Exports**: Immediately download campaigns as raw **TXT**, formatted **Markdown**, or print-ready **PDF** documents.

---

## 🛠️ Technology Stack

* **Frontend**: Streamlit, custom CSS, HTML, vanilla JavaScript clipboard integrations.
* **Backend**: FastAPI, Uvicorn, Pydantic data validation.
* **AI Engine**: Google Gemini API via LangChain.
* **Database / ORM**: Supabase PostgreSQL (Production) / SQLite (Local Fallback), SQLAlchemy.
* **Deployment**: Docker, Docker Compose.

---

## 📁 Project Structure

```text
AI_AD_CREATIVE_STUDIO/
├── backend/
│   ├── database/               # SQLAlchemy DB connection setup & models
│   │   ├── crud.py             # Database CRUD helper queries
│   │   ├── db.py               # PostgreSQL (Supabase) / SQLite connection router
│   │   └── models.py           # Campaign history schemas
│   ├── services/               # AI generation & style synthesis services
│   │   ├── loader.py           # Loads reference ad copy catalogs
│   │   ├── generator.py        # Gemini LangChain pipeline
│   │   └── compliance.py       # Policy verification rules
│   ├── main.py                 # FastAPI endpoints & routes
│   └── schemas.py              # API contract validation schemas
├── frontend/
│   └── app.py                  # Streamlit application layout, themes & styling
├── reference_ads/              # Catalog of highly converting markdown reference ads
├── reference_adsets/           # Meta target reference copies
├── requirements.txt            # Python dependencies (FastAPI, Streamlit, psycopg2, etc.)
├── Dockerfile.backend          # Docker configuration for FastAPI Backend
├── Dockerfile.frontend         # Docker configuration for Streamlit Frontend
├── docker-compose.yml          # Container orchestration service file
├── .dockerignore               # Files ignored during Docker builds
├── .gitignore                  # Files ignored by Git tracking
└── .env.example                # Template for configuration environment variables
```

---

## ⚙️ Configuration Setup

Create a `.env` file in the project root based on `.env.example`:

```env
# Database Connection String for Supabase PostgreSQL (IPv4 Connection Pooler URL)
DATABASE_URL=postgresql://postgres.meqzbsdwmsaftjeapdek:[your-password]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require

# Supabase API Settings
SUPABASE_URL=https://meqzbsdwmsaftjeapdek.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Gemini API Configurations
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash
```

*Note: Supabase direct database connection port (5432) is IPv6-only. When connecting from Docker or local networks lacking IPv6, you must use the **Connection Pooler** address (port **6543**).*

---

## 🐳 Running with Docker (Recommended)

Make sure you have **Docker Desktop** installed and running on your local machine.

1. **Build and start the application**:
   ```bash
   docker compose up --build
   ```
2. **Access the services**:
   * Streamlit Dashboard (UI): [http://localhost:8501](http://localhost:8501)
   * FastAPI Documentation (API): [http://localhost:8000/docs](http://localhost:8000/docs)
3. **Shutdown background containers**:
   ```bash
   docker compose down
   ```

---

## 🐍 Local Installation (Without Docker)

If you prefer to run the application outside of Docker:

1. **Clone the repository and create virtual environment**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate     # Windows PowerShell
   # source venv/bin/activate       # macOS / Linux
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the backend server**:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. **Start the frontend application** (in a separate terminal):
   ```bash
   streamlit run frontend/app.py
   ```

---

## 🚀 Production Deployment (VPS)

To deploy the application to your **Hostinger VPS** (running Ubuntu):

1. Connect to your VPS via SSH and install Docker.
2. Clone the repository and create your production `.env` file.
3. Start the application in detached mode:
   ```bash
   docker compose up -d
   ```
4. Configure Nginx as a reverse proxy to route traffic to the Streamlit frontend container on port `8501`.
