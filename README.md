# ◈ Digital Media Assistant (DMA)

AI-powered digital media assistant for news analysis, fact-checking, and content creation.

Built with **Streamlit** and **OpenAI GPT-4o-mini**.

---

## Features

### Core Analysis
- **Smart Article Extraction** — From URL or pasted text (trafilatura + BeautifulSoup fallback)
- **AI-Powered Analysis** — Detailed bilingual summaries (AR + EN), key points, entities, dates, keywords
- **Auto-Classification** — Automatic news categorization (politics, economy, technology, sports, health, etc.) with confidence score

### Sentiment & Tone
- **Sentiment Analysis** — Positive / Negative / Neutral with score (-1.0 to +1.0) and rationale
- **Media Tone Detection** — Objective, sensational, provocative, analytical, emotional, promotional
- **Bias Indicators** — Detects and flags potential bias in reporting

### Fake News Detection
- **Risk Score** — 0% to 100% misinformation risk assessment
- **Red Flag Indicators** — Severity-coded (High, Medium, Low)
- **Verifiable Claims** — Extracts factual claims that can be independently fact-checked
- **Missing Context** — Identifies important context not included in the article

### Coverage Comparison
- **Related Source Discovery** — Automatic search via Google News RSS
- **Deep Analysis** — Fetches and analyzes related articles with full LLM processing
- **Cross-Source Comparison** — Similarities, differences, and coverage gaps

### Credibility Assessment
- **Transparent Scoring** — Score out of 10 with detailed reasoning
- **Domain Verification** — Checks source against recognized outlets database
- **Methodology Disclosure** — Full step-by-step explanation of how the score was calculated
- **Academic References** — IFCN, Reuters Fact Check, First Draft, Google News Initiative

### Smart Chat
- **Interactive Q&A** — Ask follow-up questions about the analyzed article
- **Context-Aware** — Responds based only on the analysis and comparison data
- **Bilingual** — Responds in Arabic or English based on interface language

### Article Generation
- **Full Article Writing** — Generates a professional 500-800 word news article
- **Bilingual Output** — Available in both Arabic and English
- **Journalistic Style** — Professional tone with subheadings and structure

### Event Timeline
- **Chronological Reconstruction** — Builds a visual timeline from the article and related sources
- **Importance Levels** — Events coded by importance (High, Medium, Low)
- **Source Attribution** — Each event linked to its source

### Batch Analysis
- **Multi-Article Processing** — Analyze 2-5 news articles simultaneously
- **Comparative Overview** — Side-by-side comparison of sentiment, tone, category, and fake news risk
- **Expandable Details** — Full analysis available for each article

### Topic Monitoring
- **Custom Topics** — Add any topic to your watchlist
- **On-Demand Scanning** — Scan all monitored topics with one click
- **Smart Alerts** — Results classified by relevance, urgency, and sentiment
- **One-Line Summaries** — Bilingual quick summaries for each result

### Multi-Platform Export
- **10 Ready-to-Publish Posts** — Telegram, LinkedIn, X/Twitter, Instagram, Email Newsletter (AR + EN)
- **Direct Sharing** — Open platform with pre-filled content in one click
- **File Downloads** — Save any post as a text file
- **Full HTML Report** — Comprehensive report exportable as PDF via browser print

### User Experience
- **Bilingual Interface** — Full Arabic and English UI with one-click toggle
- **Dark / Light Theme** — Switch between themes from the sidebar
- **Analysis History** — Track all previous analyses in the sidebar
- **Progress Indicators** — Real-time feedback during analysis

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Configuration

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"
```

Or use environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| LLM | OpenAI GPT-4o-mini |
| Article Extraction | trafilatura + BeautifulSoup |
| News Search | Google News RSS |
| Language | Python 3.9+ |

---

Built with DMA
