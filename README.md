

```markdown
# 🛡️ Price Aggregator

### *Autonomous Cross-Platform Commerce Data Pipelines & Real-Time Price Optimization Engine*

<div align="center">

| 🚀 Performance | 🛡️ Reliability | ⚡ Automation | 📊 Analytics |
|:-------------:|:--------------:|:------------:|:-----------:|
| Async Playwright | Semantic Extraction | Daily Scheduler | Historical Trends |
| JSON-LD Parsing | Spec Validation | Cross Platform | Price Intelligence |

</div>

---

# 💼 The Interview Pitch

The **Price Aggregator** is a production-grade, highly resilient data harvesting and price intelligence platform engineered to track, map, and analyze competitive retail dynamics across 100+ global digital commerce nodes simultaneously. 

Unlike fragile traditional web scrapers that rely on hardcoded, volatile CSS selectors, this system implements a **Tiered Semantic Extraction Engine** that bypasses DOM mutations by natively targeting structured schema layer definitions (JSON-LD Microdata and OpenGraph protocols). To overcome the asynchronous rendering challenges of modern Single Page Applications (SPAs), the extraction pipeline utilizes an asynchronous **Playwright Stealth Architecture** running isolated, resource-blocked browser contexts that complete deep DOM scans within a strict 12-second execution window. 

Data is validated by a defensive **Levenshtein-based Spec-Override Engine** that completely prevents cross-product data pollution by enforcing high-confidence identifier vetoes. The system functions autonomously as a "set-and-forget" local appliance via a dynamic, cross-platform background task runner utility that silently aggregates metrics daily, updates a high-performance transactional SQLite ledger, and pushes real-time event alerts directly across localized and remote notification channels.

---

# ⚙️ Feature Overview

| Feature | Description |
|----------|-------------|
| 🌍 **Multi-Platform Tracking** | Monitor 100+ global and regional e-commerce domains from a single dashboard. |
| 🧠 **Semantic Extraction Engine** | Extracts data using JSON-LD, Microdata & OpenGraph instead of fragile CSS selectors. |
| ⚡ **Async Playwright Engine** | High-speed asynchronous scraping with stealth browser contexts and anti-bot mitigation. |
| 🔍 **Spec-Override Validation** | Prevents mismatched products using Levenshtein similarity + specification veto traps. |
| 📈 **Historical Analytics** | Interactive charts with price history, volatility calculators, and trend analysis. |
| 🔔 **Smart Alerts Hub** | Multi-channel notifications via Windows desktop toasts & Discord webhooks. |
| 💾 **SQLite Ledger** | Persistent WAL-mode database optimized for historical tracking and fast querying. |
| 🤖 **Autonomous Scheduler** | Runs automatically every day at 9:00 AM across Windows, Linux, and macOS. |

---

# 🧩 System Architecture

```text
                        ┌──────────────────────┐
                        │  Product URLs Input  │
                        └──────────┬───────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │ Async Playwright Stealth Engine│
                  └──────────┬─────────────────────┘
                             │
                             ▼
               ┌──────────────────────────────────┐
               │ Tiered Semantic Extraction Engine│
               │  JSON-LD • Microdata • OpenGraph │
               └──────────┬───────────────────────┘
                          │
                          ▼
          ┌────────────────────────────────────────┐
          │ Spec-Override Validation Engine        │
          │ Levenshtein + Product Identifier Check │
          └──────────┬─────────────────────────────┘
                     │
         ┌───────────┴────────────┐
         ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│ SQLite Database  │     │ Notification Hub │
│ Historical Data  │     │ Discord/Desktop  │
└─────────┬────────┘     └──────────────────┘
          │
          ▼
┌────────────────────────────────────────────┐
│ Streamlit Analytics Dashboard              │
│ • Aggregator Matrix                        │
│ • Historical Trends & Volatility           │
│ • Engine Diagnostics                       │
└────────────────────────────────────────────┘

```

---

# 📊 Dashboard Modules

| Module | Purpose | Key Features |
| --- | --- | --- |
| 🛒 **Aggregator Matrix** | Compare multiple stores simultaneously. | URL ingestion, automated metric cards, and green-highlighted best deals. |
| 📉 **Historical Trends** | View long-term pricing and volatility. | Multi-line trajectory overlays and floor-to-ceiling percentage drop calculators. |
| 🖥 **Engine Diagnostics** | Monitor scraping health and latency. | Real-time status check grids, HTTP response monitoring, and layout warnings. |

---

# 🛡️ Reliability Features

* ✅ CSS-selector independent extraction
* ✅ SPA & dynamic JavaScript compatible architecture
* ✅ Headless stealth browser execution with anti-bot mitigation
* ✅ 1,500ms dynamic DOM hydration fallback
* ✅ Hardcoded Veto Traps preventing product tier/capacity mismatches
* ✅ Cross-platform scheduler (Windows Task Scheduler & Unix Cron)
* ✅ WAL-mode transactional SQLite database
* ✅ UTF-8 terminal encoding safety protocols

---

# 📂 Project Structure

```text
Price-Aggregator/
│
├── core/
│   └── scraper.py              # Playwright stealth driver & 3-Tier semantic engine
│
├── dashboard/
│   └── app.py                  # Streamlit 3-tab analytics workspace & 100+ platform registry
│
├── alerts/
│   └── notifier.py             # Windows Desktop toast & Discord webhook integrations
│
├── logs/
│   └── price_history.db        # Transactional SQLite ledger (WAL mode)
│
├── tests/
│   └── test_audit.py           # Automated SDET verification & QA suite
│
├── main.py                     # Daily background orchestrator & execution pipeline
├── matcher.py                  # Levenshtein fuzzy logic & Spec-Override veto engine
├── setup_scheduler.py          # Cross-platform OS automation installer (Win/Linux/Mac)
├── run_daily_tracker.ps1       # Windows PowerShell background wrapper script
├── requirements.txt            # Project dependency packages
└── README.md                   # System documentation

```

---

# 📈 Pipeline Lifecycle

```text
Product URL Ingestion
      │
      ▼
Launch Sandboxed Browser
      │
      ▼
Semantic Metadata Extraction
      │
      ▼
Specification Veto Validation
      │
      ▼
Store in SQLite Ledger
      │
      ▼
Update UI Matrix & Charts
      │
      ▼
Evaluate Threshold Alerts
      │
      ▼
Scheduled Daily Execution (09:00 AM)

```

---

# 🎯 Key Engineering Highlights

### 🔍 Extraction Engine

* **JSON-LD Microdata Parser**
* **OpenGraph Protocol Mapping**
* **Regex Currency Fallback**
* **SPA Hydration Delays**
* **Network Asset Blocking**

### ⚙️ Algorithmic Processing

* **Async Context Isolation**
* **Levenshtein String Distance**
* **Capacity & Tier Veto Traps**
* **Time-Series Volatility Math**
* **Multi-Channel Alerting**

---

# 📦 Installation & Setup

> **Note:** Ensure you have **Python 3.10+** installed on your system before proceeding.

### 1. Clone the Repository

```bash
git clone [https://github.com/Guptha0/Price-Aggregator.git](https://github.com/Guptha0/Price-Aggregator.git)
cd Price-Aggregator

```

### 2. Instantiate Environment & Install Dependencies

**For Windows Deployment:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

```

**For Linux / macOS Deployment:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

```

### 3. Launch the Streamlit Interactive Workspace

```bash
streamlit run dashboard/app.py

```

### 4. Deploy the Autonomous Daily Background Task Runner (9:00 AM)

Run the dynamic installation script to register the headless cron runner into your operating system's kernel registry:

```bash
# To install the background cron task automatically
python setup_scheduler.py --install

# To completely strip the background task from the operating system
python setup_scheduler.py --remove

```

---

# 🚀 Future Roadmap

* [ ] AI-powered price forecasting and drop predictions
* [ ] FastAPI backend for remote REST endpoints
* [ ] Containerization via Docker & Docker Compose
* [ ] Migration path to PostgreSQL for multi-user enterprise scaling
* [ ] Redis in-memory caching for sub-second UI renders
* [ ] Cloud deployment templates (AWS EC2 / GCP)

---

# ⭐ Support the Project

If you found this architecture or data extraction pipeline useful, please consider giving the repository a ⭐ on GitHub to support future development!

```

```
