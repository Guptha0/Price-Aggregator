# 🛡️ Price Aggregator

### *Autonomous Cross-Platform Commerce Data Pipelines & Real-Time Price Optimization Engine*

---

## 💼 The Interview Pitch

The **Price Aggregator** is a production-grade, highly resilient data harvesting and price intelligence platform engineered to track, map, and analyze competitive retail dynamics across 100+ global digital commerce nodes simultaneously. 

Unlike fragile traditional web scrapers that rely on hardcoded, volatile CSS selectors, this system implements a **Tiered Semantic Extraction Engine** that bypasses DOM mutations by natively targeting structured schema layer definitions (JSON-LD Microdata and OpenGraph protocols). To overcome the asynchronous rendering challenges of modern Single Page Applications (SPAs), the extraction pipeline utilizes an asynchronous **Playwright Stealth Architecture** running isolated, resource-blocked browser contexts that complete deep DOM scans within a strict 12-second execution window. 

Data is validated by a defensive **Levenshtein-based Spec-Override Engine** that completely prevents cross-product data pollution by enforcing high-confidence identifier vetoes. The system functions autonomously as a "set-and-forget" local appliance via a dynamic, cross-platform background task runner utility that silently aggregates metrics daily, updates a high-performance transactional SQLite ledger, and pushes real-time event alerts directly across localized and remote notification channels.

---

## 🛠️ Technical Architecture & Stack

### System Workflow Diagram
```text
 ┌────────────────┐      ┌─────────────────┐      ┌──────────────────┐
 │ Target Commerce│ ───> │  Playwright     │ ───> │  3-Tier Semantic │
 │ URL Ingestion  │      │  Stealth Engine │      │  Extractor Pool  │
 └────────────────┘      └─────────────────┘      └──────────────────┘
                                                            │
                                                            ▼
 ┌────────────────┐      ┌─────────────────┐      ┌──────────────────┐
 │ Streamlit Tabs │ <─── │ Transactional   │ <─── │ Spec-Override    │
 │ UI Dashboard   │      │ SQLite Ledger   │      │ Matcher (Veto)   │
 └────────────────┘      └─────────────────┘      └──────────────────┘
         │                                                  │
         ▼                                                  ▼
 ┌────────────────┐                               ┌──────────────────┐
 │ Live UI Alerts │                               │ Native Windows / │
 │ & Visual Matrix│                               │ Discord Alerts   │
 └────────────────┘                               └──────────────────┘
Core Technologies
Automation Engine: Playwright + Playwright-Stealth (Async API running headless sandboxed browser context isolation).

Fuzzy Algorithmic Logic: thefuzz (Levenshtein Distance text similarity paired with deterministic specifications validation).

Data Pipeline: pandas (Dynamic matrix formatting, variance computation, and multi-line time-series structuring).

Storage Architecture: SQLite (Transactional ledger running Write-Ahead Logging [WAL] mode with optimized indexing).

Frontend UI: Streamlit (High-performance multi-tab data visualization workspace).

✨ Core Features
100+ Pre-Populated Platform Registry: A hardcoded autocomplete platform tracking pool encompassing major fashion, technology, grocery, and marketplace sectors globally (Amazon, Flipkart, Meesho, Croma, Walmart, Myntra, Nykaa, eBay, and more).

3-Tab Advanced Analytics Interface:

Tab 1: Aggregator Matrix: Seamless multi-source product URL ingestion, automated live metric summaries, and a side-by-side transaction matrix that dynamically highlights the best market deal in real-time.

Tab 2: Historical Trend Intelligence: Interactive overlays tracking long-term price trajectories alongside an automated Price Volatility Calculator mapping floor-to-ceiling percentage drops.

Tab 3: Engine Diagnostics: Real-time hardware and network scrape status check grids indicating active health signals, response latency, and layout warnings.

Spec-Override Veto Logic: Defensive identifier grouping routines that prevent mismatched product variants (e.g., separating 1TB vs 2TB components or PRO vs EVO hardware models) while lowering text thresholds dynamically to accommodate padded brand aliases.

Unified OS Scheduling Utility: A native platform-agnostic configuration installer (setup_scheduler.py) that instantly registers the pipeline into system cron daemons or the Windows Task Scheduler registry via one-line terminal initializations.

📦 Installation & Setup
Ensure you have Python 3.10+ installed on your system before proceeding.

1. Clone the Repository
Bash
git clone [https://github.com/Guptha0/universal-price-aggregator.git](https://github.com/Guptha0/universal-price-aggregator.git)
cd universal-price-aggregator
2. Instantiate Environment & Install Dependencies
PowerShell
# Windows Deployment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

# Linux / macOS Deployment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
3. Launch the Streamlit Interactive Workspace
Bash
streamlit run dashboard/app.py
4. Deploy the Autonomous Daily Background Task Runner (9:00 AM)
Run the dynamic installation script to register the headless cron runner into your operating system's kernel registry:

Bash
# To install the background cron task automatically
python setup_scheduler.py --install

# To completely strip the background task from the operating system
python setup_scheduler.py --remove

---

### How to Update This on GitHub Right Now
You can update your README directly from your terminal in three quick steps:
1. Open your project file `README.md` locally in your code editor and paste the text above into it.
2. Save the file.
3. In your PowerShell window, run:
   ```powershell
   git add README.md
   git commit -m "docs: rebrand to Price Aggregator and polish documentation"
   git push
