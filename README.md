# 🍽️ AI-Powered Restaurant Recommendation System

An AI-powered restaurant recommendation service inspired by **Zomato** that intelligently suggests restaurants based on user preferences using structured data combined with a **Large Language Model (LLM)**.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd <project-folder>

# 2. Create a virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# 5. Run the application
python -m src.app
```

The app will start at **http://localhost:5000**.

---

## 📂 Project Structure

```
project-root/
├── docs/
│   ├── problemstatement.md      # Problem statement
│   ├── phased-architecture.md   # Phase-wise architecture
│   └── edge-cases.md            # Detailed edge cases
├── data/                        # Downloaded datasets
├── src/
│   ├── __init__.py
│   ├── app.py                   # Flask web application
│   ├── config.py                # Configuration loader
│   ├── utils.py                 # Shared utilities
│   ├── static/
│   │   ├── style.css            # Stylesheet
│   │   └── script.js            # Client-side JS
│   └── templates/
│       ├── index.html           # Input form
│       └── results.html         # Recommendations display
├── tests/
│   └── __init__.py
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
└── README.md
```

---

## 🏗️ Architecture Phases

| Phase | Description | Status |
|-------|-------------|--------|
| **0** | Project Setup & Basic Web UI | ✅ Complete |
| **1** | Data Ingestion & Preprocessing | ⬜ Pending |
| **2** | Filtering & Matching Engine | ⬜ Pending |
| **3** | LLM Integration & Recommendations | ⬜ Pending |
| **4** | UI Polish & Deployment | ⬜ Pending |

See [docs/phased-architecture.md](docs/phased-architecture.md) for full details.

---

## ⚙️ Configuration

All settings are managed via the `.env` file. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM service (`openai` / `gemini` / `ollama`) | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `APP_PORT` | Web server port | `5000` |
| `DATASET_NAME` | Hugging Face dataset ID | `ManikaSaini/zomato-restaurant-recommendation` |
| `MAX_RECOMMENDATIONS` | Number of recommendations to show | `5` |

---

## 📖 Documentation

- [Problem Statement](docs/problemstatement.md)
- [Phased Architecture](docs/phased-architecture.md)
- [Edge Cases](docs/edge-cases.md)

---

## 🛠️ Tech Stack

- **Python 3.10+** — Core language
- **Flask** — Web framework
- **Pandas** — Data processing
- **Hugging Face Datasets** — Data source
- **OpenAI / Gemini / Ollama** — LLM providers
- **RapidFuzz** — Fuzzy string matching

---

## 📄 License

This project is for educational purposes.
