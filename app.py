import os
import re
import json
import html
from datetime import datetime
from urllib.parse import quote_plus, urlparse

import feedparser
import requests
import streamlit as st
from bs4 import BeautifulSoup

try:
    import trafilatura
except Exception:
    trafilatura = None

from openai import OpenAI

st.set_page_config(page_title="Digital Media Assistant", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

DARK_VARS = """--bg-primary:#0a0a0f;--bg-secondary:#12121a;--bg-card:#1a1a26;--bg-card-hover:#22222f;--accent-primary:#6c63ff;--accent-secondary:#ff6b6b;--accent-green:#2dd4a8;--accent-amber:#f5a623;--accent-blue:#4da6ff;--text-primary:#f0eff4;--text-secondary:#9896a6;--text-muted:#5e5c6e;--border-color:#2a2a3a;"""
LIGHT_VARS = """--bg-primary:#f7f7fb;--bg-secondary:#ffffff;--bg-card:#ffffff;--bg-card-hover:#f0eef6;--accent-primary:#6c63ff;--accent-secondary:#e74c3c;--accent-green:#0a8a6a;--accent-amber:#d4850a;--accent-blue:#2563eb;--text-primary:#1a1a2e;--text-secondary:#555568;--text-muted:#8888a0;--border-color:#ddd8ee;"""

tv = DARK_VARS if st.session_state.theme == "dark" else LIGHT_VARS

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600;700&family=Noto+Kufi+Arabic:wght@300;400;500;600;700&display=swap');
:root{{{tv}}}
.stApp{{background-color:var(--bg-primary)!important;font-family:'DM Sans','Noto Kufi Arabic',sans-serif!important;color:var(--text-primary)!important}}
#MainMenu,footer,header{{visibility:hidden}}.stDeployButton{{display:none}}
.block-container{{padding:2rem 3rem!important;max-width:1400px!important}}
.hero-header{{text-align:center;padding:2.5rem 2rem 1.5rem;position:relative}}
.hero-header::before{{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);width:120px;height:3px;background:linear-gradient(135deg,#6c63ff,#4da6ff);border-radius:2px}}
.hero-title{{font-family:'Playfair Display','Noto Kufi Arabic',serif;font-size:2.6rem;font-weight:800;background:linear-gradient(135deg,#6c63ff,#4da6ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero-subtitle{{color:var(--text-secondary);font-size:1rem;font-weight:300}}
.section-header{{font-family:'Playfair Display','Noto Kufi Arabic',serif;font-size:1.4rem;font-weight:700;color:var(--text-primary);margin:1.5rem 0 .8rem;padding-bottom:.4rem;border-bottom:2px solid var(--border-color)}}
.metric-card{{background:var(--bg-card);border:1px solid var(--border-color);border-radius:14px;padding:1.3rem;text-align:center;transition:all .3s}}
.metric-card:hover{{border-color:var(--accent-primary);transform:translateY(-2px)}}
.metric-value{{font-family:'Playfair Display',serif;font-size:1.8rem;font-weight:800;background:linear-gradient(135deg,#6c63ff,#4da6ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.metric-label{{color:var(--text-secondary);font-size:.78rem;font-weight:500;text-transform:uppercase;letter-spacing:1px;margin-top:.2rem}}
.category-badge{{display:inline-block;padding:.4rem 1.2rem;border-radius:25px;font-size:.9rem;font-weight:700;letter-spacing:.5px;margin:.3rem}}
.cat-politics{{background:rgba(108,99,255,.15);color:var(--accent-primary);border:1px solid rgba(108,99,255,.3)}}
.cat-economy{{background:rgba(45,212,168,.15);color:var(--accent-green);border:1px solid rgba(45,212,168,.3)}}
.cat-sports{{background:rgba(245,166,35,.15);color:var(--accent-amber);border:1px solid rgba(245,166,35,.3)}}
.cat-technology{{background:rgba(77,166,255,.15);color:var(--accent-blue);border:1px solid rgba(77,166,255,.3)}}
.cat-health{{background:rgba(255,107,107,.15);color:var(--accent-secondary);border:1px solid rgba(255,107,107,.3)}}
.cat-default{{background:rgba(152,150,166,.15);color:var(--text-secondary);border:1px solid rgba(152,150,166,.3)}}
.fake-alert{{border-radius:14px;padding:1.5rem;margin:1rem 0;text-align:center}}
.fake-alert-high{{border:2px solid #ff4444;background:rgba(255,68,68,.1)}}
.fake-alert-mid{{border:2px solid var(--accent-amber);background:rgba(245,166,35,.08)}}
.fake-alert-low{{border:2px solid var(--accent-green);background:rgba(45,212,168,.08)}}
.fake-score{{font-family:'Playfair Display',serif;font-size:2.5rem;font-weight:800}}
.fake-indicator{{background:var(--bg-secondary);border-left:3px solid var(--accent-secondary);padding:.6rem 1rem;margin:.4rem 0;border-radius:0 8px 8px 0;font-size:.88rem;color:var(--text-secondary)}}
.cred-gauge{{background:var(--bg-card);border:1px solid var(--border-color);border-radius:16px;padding:2rem;text-align:center;margin:1rem 0}}
.cred-score{{font-family:'Playfair Display',serif;font-size:3.5rem;font-weight:800;line-height:1}}
.cred-score-high{{color:var(--accent-green)}}.cred-score-mid{{color:var(--accent-amber)}}.cred-score-low{{color:var(--accent-secondary)}}
.cred-label{{font-size:.85rem;font-weight:600;margin-top:.4rem;letter-spacing:1px;text-transform:uppercase}}
.cred-bar{{height:8px;border-radius:4px;background:var(--bg-secondary);margin:1rem auto 0;max-width:300px;overflow:hidden}}
.cred-bar-fill{{height:100%;border-radius:4px;transition:width 1s}}
.entity-tag{{display:inline-block;padding:.3rem .7rem;margin:.2rem;border-radius:8px;font-size:.82rem;font-weight:500;background:var(--bg-secondary);border:1px solid var(--border-color);color:var(--text-primary)}}
.source-card{{background:var(--bg-card);border:1px solid var(--border-color);border-radius:14px;padding:1.3rem;margin-bottom:.8rem;border-left:3px solid var(--accent-primary)}}
.source-title{{font-weight:600;font-size:1rem;color:var(--text-primary)}}.source-meta{{color:var(--text-muted);font-size:.78rem}}
.export-card{{background:var(--bg-card);border:1px solid var(--border-color);border-radius:14px;padding:1.3rem;margin-bottom:.8rem}}
.export-platform{{font-weight:700;font-size:1rem;display:flex;align-items:center;gap:.5rem}}
.method-step{{background:var(--bg-secondary);border-left:3px solid var(--accent-primary);padding:.7rem 1rem;margin:.4rem 0;border-radius:0 8px 8px 0;font-size:.88rem;color:var(--text-secondary)}}
.chat-msg{{padding:.8rem 1rem;margin:.5rem 0;border-radius:12px;font-size:.92rem;line-height:1.6}}
.chat-user{{background:var(--accent-primary);color:white;margin-left:20%;text-align:right}}
.chat-bot{{background:var(--bg-card);color:var(--text-primary);margin-right:20%;border:1px solid var(--border-color)}}
section[data-testid="stSidebar"]{{background-color:var(--bg-secondary)!important;border-right:1px solid var(--border-color)!important}}
.stTabs [data-baseweb="tab-list"]{{gap:0;background:var(--bg-secondary);border-radius:12px;padding:4px;border:1px solid var(--border-color)}}
.stTabs [data-baseweb="tab"]{{border-radius:10px;padding:.5rem 1rem;font-weight:600;font-size:.83rem;color:var(--text-secondary);background:transparent;border:none}}
.stTabs [aria-selected="true"]{{background:var(--accent-primary)!important;color:white!important}}
.stButton>button{{background:linear-gradient(135deg,#6c63ff,#4da6ff)!important;color:white!important;border:none!important;border-radius:12px!important;padding:.65rem 1.8rem!important;font-weight:600!important;font-size:.92rem!important;box-shadow:0 4px 15px rgba(108,99,255,.3)!important}}
.stButton>button:hover{{transform:translateY(-2px)!important;box-shadow:0 6px 20px rgba(108,99,255,.4)!important}}
.stDownloadButton>button{{background:var(--bg-card)!important;color:var(--text-primary)!important;border:1px solid var(--border-color)!important;border-radius:10px!important}}
.stTextInput>div>div>input,.stTextArea>div>div>textarea{{background:var(--bg-card)!important;border:1px solid var(--border-color)!important;border-radius:10px!important;color:var(--text-primary)!important}}
.stRadio label{{background:var(--bg-card)!important;border:1px solid var(--border-color)!important;border-radius:10px!important;color:var(--text-primary)!important}}
::-webkit-scrollbar{{width:6px}}::-webkit-scrollbar-track{{background:var(--bg-primary)}}::-webkit-scrollbar-thumb{{background:var(--border-color);border-radius:3px}}
hr{{border-color:var(--border-color)!important}}
</style>""", unsafe_allow_html=True)

# ── Constants ──
TRUSTED_DOMAINS={"bbc.com","bbc.co.uk","reuters.com","apnews.com","cnn.com","aljazeera.com","aljazeera.net","skynewsarabia.com","alarabiya.net","nytimes.com","theguardian.com","washingtonpost.com","npr.org","france24.com","dw.com","spa.gov.sa","aawsat.com","independent.co.uk","bloomberg.com","ft.com","economist.com","foreignpolicy.com","politico.com","axios.com"}
VERIFICATION_REFERENCES=["International Fact-Checking Network (IFCN)","Reuters Fact Check methodology","First Draft verification guidance","Google News Initiative Trust Toolkit"]
CAT_COLORS={"politics":"cat-politics","economy":"cat-economy","business":"cat-economy","sports":"cat-sports","technology":"cat-technology","tech":"cat-technology","health":"cat-health","science":"cat-technology","entertainment":"cat-sports","environment":"cat-health","education":"cat-economy"}
CAT_ICONS={"politics":"🏛️","economy":"💰","business":"💼","sports":"⚽","technology":"💻","tech":"💻","health":"🏥","science":"🔬","entertainment":"🎬","environment":"🌍","education":"📚","military":"⚔️","culture":"🎭","legal":"⚖️"}
HEADERS={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

# ── Helpers ──
def get_api_key():
    try: k=st.secrets.get("OPENAI_API_KEY","")
    except: k=""
    return k or os.getenv("OPENAI_API_KEY","")

def get_model():
    try: m=st.secrets.get("OPENAI_MODEL","")
    except: m=""
    return m or os.getenv("OPENAI_MODEL","gpt-4o-mini")

def build_client(): return OpenAI(api_key=get_api_key())

def clean_text(t):
    if not t: return ""
    return re.sub(r"\s+"," ",html.unescape(t)).strip()

def extract_domain(u): return urlparse(u).netloc.replace("www.","").lower()

def extract_article(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=20); r.raise_for_status(); hc=r.text
    except Exception as e:
        return {"title":"","text":"","error":str(e)}
    title=text=""
    try:
        soup=BeautifulSoup(hc,"html.parser")
        if soup.title and soup.title.string: title=clean_text(soup.title.string)
    except: pass
    if trafilatura:
        try:
            dl=trafilatura.fetch_url(url)
            if dl:
                ex=trafilatura.extract(dl,include_comments=False,include_tables=False)
                if ex: text=clean_text(ex)
        except: pass
    if not text:
        try: text=clean_text(" ".join(p.get_text(" ",strip=True) for p in BeautifulSoup(hc,"html.parser").find_all("p")))
        except: pass
    return {"title":title,"text":text,"url":url,"error":""}

# ── LLM ──
def _parse_json(raw):
    raw=re.sub(r"^```json\s*","",raw.strip()); raw=re.sub(r"\s*```$","",raw)
    try: return json.loads(raw)
    except:
        m=re.search(r"(\{.*\})",raw,re.S)
        if m:
            try: return json.loads(m.group(1))
            except: pass
    return {}

def llm_json(sys,usr,temp=0.1):
    c=build_client(); r=c.chat.completions.create(model=get_model(),temperature=temp,messages=[{"role":"system","content":sys},{"role":"user","content":usr}])
    return _parse_json(r.choices[0].message.content.strip())

def llm_text(sys,usr,temp=0.2):
    c=build_client(); r=c.chat.completions.create(model=get_model(),temperature=temp,messages=[{"role":"system","content":sys},{"role":"user","content":usr}])
    return r.choices[0].message.content.strip()

def llm_chat(msgs,temp=0.3):
    c=build_client(); r=c.chat.completions.create(model=get_model(),temperature=temp,messages=msgs)
    return r.choices[0].message.content.strip()

# ── Analysis ──
def analyze_article(title,text):
    sys="You are a world-class digital media analyst and fact-checker. Return valid JSON only."
    usr=f"""Article title: {title}
Article text: {text[:15000]}

Return JSON:
{{"main_event":"","detailed_summary_en":"150-250 words","detailed_summary_ar":"150-250 كلمة",
"key_points":[],"prominent_people":[],"organizations":[],"locations":[],"dates":[],
"sentiment":"positive/negative/neutral","sentiment_score":"float -1 to 1",
"sentiment_rationale_en":"","sentiment_rationale_ar":"",
"media_tone":"objective/sensational/provocative/analytical/emotional/promotional",
"media_tone_rationale_en":"","media_tone_rationale_ar":"","bias_indicators":[],
"category":"politics/economy/technology/sports/health/science/entertainment/environment/education/military/culture/legal/other",
"category_confidence":"float 0-1","sub_categories":[],
"fake_news_risk_score":"float 0-1","fake_news_indicators":[{{"indicator":"","severity":"high/medium/low"}}],
"fake_news_assessment_en":"","fake_news_assessment_ar":"",
"factual_claims":[],"missing_context":[],
"search_query":"","keywords":[]}}"""
    result=llm_json(sys,usr)
    defs={"main_event":"","detailed_summary_en":"","detailed_summary_ar":"","key_points":[],"prominent_people":[],"organizations":[],"locations":[],"dates":[],"sentiment":"neutral","sentiment_score":0.0,"sentiment_rationale_en":"","sentiment_rationale_ar":"","media_tone":"objective","media_tone_rationale_en":"","media_tone_rationale_ar":"","bias_indicators":[],"category":"other","category_confidence":0.5,"sub_categories":[],"fake_news_risk_score":0.5,"fake_news_indicators":[],"fake_news_assessment_en":"","fake_news_assessment_ar":"","factual_claims":[],"missing_context":[],"search_query":title,"keywords":[]}
    for k,v in defs.items():
        if k not in result: result[k]=v
    return result

# ── Sources ──
def search_sources(query,limit=8,lang="en",country="US"):
    url=f"https://news.google.com/rss/search?q={quote_plus(query)}&hl={lang}-{country}&gl={country}&ceid={country}:{lang}"
    feed=feedparser.parse(url); items=[]
    for e in feed.entries[:limit*2]:
        sn=""
        if hasattr(e,"source"):
            if isinstance(e.source,dict): sn=e.source.get("title","")
            elif hasattr(e.source,"title"): sn=getattr(e.source,"title","")
        lk=getattr(e,"link","")
        if lk:
            items.append({"title":clean_text(getattr(e,"title","")),"link":lk,"published":getattr(e,"published",""),"source":sn,"summary":clean_text(getattr(e,"summary",""))})
        if len(items)>=limit: break
    return items

def deep_analyze_sources(sources,orig_url,max_n=3):
    out=[]
    for s in sources:
        if s["link"]==orig_url or len(out)>=max_n: continue
        try:
            a=extract_article(s["link"])
            if a.get("error") or not a.get("text"): continue
            an=analyze_article(a["title"],a["text"])
            an["_src"]=s.get("source",""); an["_url"]=s["link"]; an["_pub"]=s.get("published","")
            out.append(an)
        except: continue
    return out

# ── Comparison ──
def compare_coverage(primary,related):
    if not related:
        return {"similarities":[],"differences":[],"coverage_gaps":[],"comparison_summary_en":"No sources analyzed.","comparison_summary_ar":"لم يتم تحليل مصادر."}
    sys="You are a media comparison analyst. Return valid JSON only."
    usr=f"""Analyses: {json.dumps({"primary":primary,"related":related},ensure_ascii=False)[:12000]}
Return JSON: {{"similarities":[],"differences":[],"coverage_gaps":[],"comparison_summary_en":"","comparison_summary_ar":""}}"""
    r=llm_json(sys,usr,0.2)
    for k in ["similarities","differences","coverage_gaps","comparison_summary_en","comparison_summary_ar"]:
        if k not in r: r[k]=[] if k!="comparison_summary_en" and k!="comparison_summary_ar" else ""
    return r

# ── Credibility ──
def build_credibility(url,rel_count,comp,fake_s=0.5):
    domain=extract_domain(url); score=0; ren=[]; rar=[]
    if domain in TRUSTED_DOMAINS:
        score+=3; ren.append("Recognized news outlet."); rar.append("مؤسسة إخبارية معروفة.")
    else:
        score+=1; ren.append("Unknown domain — verify independently."); rar.append("نطاق غير معروف — تحقق إضافي مطلوب.")
    if rel_count>=2: score+=3; ren.append("Multiple sources confirm."); rar.append("عدة مصادر تؤكد.")
    elif rel_count==1: score+=2; ren.append("One source for comparison."); rar.append("مصدر واحد للمقارنة.")
    else: ren.append("No comparison sources."); rar.append("لا مصادر مقارنة.")
    ov=len(comp.get("similarities",[])); df=len(comp.get("differences",[]))
    if ov>=2: score+=2; ren.append("Strong cross-source consistency."); rar.append("اتساق قوي بين المصادر.")
    elif ov==1: score+=1; ren.append("Limited overlap."); rar.append("تشابه محدود.")
    if df>0: score+=1; ren.append("Differences transparently shown."); rar.append("الاختلافات معروضة بشفافية.")
    if fake_s<=0.2: score+=1; ren.append("Low misinformation risk."); rar.append("خطر تضليل منخفض.")
    elif fake_s>=0.7: score=max(score-2,0); ren.append("High misinformation risk — caution."); rar.append("خطر تضليل مرتفع — حذر.")
    score=min(score,10)
    le,la=("High","مرتفع") if score>=8 else (("Moderate","متوسط") if score>=5 else ("Low","منخفض"))
    men=["Analyzed source domain.","Searched Google News RSS.","LLM entity extraction.","Cross-source comparison.","Fake news risk assessment.","Full methodology disclosure."]
    mar=["تحليل نطاق المصدر.","بحث Google News RSS.","استخراج كيانات بالذكاء الاصطناعي.","مقارنة عبر المصادر.","تقييم خطر التضليل.","إفصاح كامل عن المنهجية."]
    return {"score":score,"level_en":le,"level_ar":la,"domain":domain,"reasons_en":ren,"reasons_ar":rar,"method_en":men,"method_ar":mar,"references":VERIFICATION_REFERENCES}

# ── Export Posts ──
def gen_posts(analysis,comp):
    sys="""You are a professional social media content creator.
Generate platform-ready posts for ALL platforms listed below.
IMPORTANT: Every single field must have content - do NOT leave any field empty.
Return valid JSON only."""

    main_event=analysis.get("main_event","")
    summary_en=analysis.get("detailed_summary_en","")
    summary_ar=analysis.get("detailed_summary_ar","")
    kps=", ".join(analysis.get("key_points",[])[:5])

    usr=f"""Main event: {main_event}
English summary: {summary_en[:1500]}
Arabic summary: {summary_ar[:1500]}
Key points: {kps}
Comparison: {json.dumps(comp,ensure_ascii=False)[:1500]}

Generate a post for EVERY platform below. All fields MUST have content:

Return JSON:
{{
  "telegram_ar": "بوست تيليقرام بالعربية مختصر ومباشر مع إيموجي مناسب وهاشتاقات",
  "telegram_en": "Telegram post in English, concise and direct with emoji and hashtags",
  "linkedin_en": "Professional LinkedIn post in English, 150-200 words, insightful analysis with hashtags",
  "linkedin_ar": "بوست لينكدإن احترافي بالعربية 150-200 كلمة مع تحليل وهاشتاقات",
  "x_post_en": "X/Twitter post under 280 characters with hashtags",
  "x_post_ar": "بوست X/تويتر أقل من 280 حرف مع هاشتاقات",
  "instagram_caption_en": "Instagram caption with storytelling style and 5+ hashtags",
  "instagram_caption_ar": "كابشن إنستقرام جذاب بأسلوب قصصي مع 5 هاشتاقات على الأقل",
  "email_newsletter_en": "Email newsletter paragraph, professional and informative",
  "email_newsletter_ar": "فقرة نشرة بريدية بالعربية احترافية وإخبارية"
}}"""
    return llm_json(sys,usr,0.35)

# ── Article Generation ──
def gen_article(analysis,comp,lang="en"):
    sys="You are a professional journalist. Write a comprehensive article based on analysis data."
    if lang=="ar":
        usr=f"اكتب مقالاً صحفياً بالعربية (500-800 كلمة) بأسلوب مهني.\n\nالتحليل:\n{json.dumps(analysis,ensure_ascii=False)[:6000]}\n\nالمقارنة:\n{json.dumps(comp,ensure_ascii=False)[:3000]}"
    else:
        usr=f"Write a news article in English (500-800 words).\n\nAnalysis:\n{json.dumps(analysis,ensure_ascii=False)[:6000]}\n\nComparison:\n{json.dumps(comp,ensure_ascii=False)[:3000]}"
    return llm_text(sys,usr,0.3)

# ── HTML Report ──
def gen_report_html(an,comp,cred,srcs):
    now=datetime.now().strftime("%Y-%m-%d %H:%M")
    kp="".join(f"<li>{p}</li>" for p in an.get("key_points",[]))
    sm="".join(f"<li>{s}</li>" for s in comp.get("similarities",[]))
    df="".join(f"<li>{d}</li>" for d in comp.get("differences",[]))
    cr="".join(f"<li>{r}</li>" for r in cred.get("reasons_en",[]))
    fi="".join(f"<li>[{i.get('severity','').upper()}] {i.get('indicator','')}</li>" for i in an.get("fake_news_indicators",[]) if isinstance(i,dict))
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>DMA Report</title>
<style>body{{font-family:'Segoe UI',sans-serif;margin:40px;color:#222;line-height:1.7}}h1{{color:#6c63ff;border-bottom:3px solid #6c63ff;padding-bottom:8px}}h2{{color:#333;margin-top:28px;border-left:4px solid #6c63ff;padding-left:12px}}.score-box{{background:#f5f3ff;border:2px solid #6c63ff;border-radius:12px;padding:20px;text-align:center;margin:20px 0}}.score-num{{font-size:3rem;font-weight:800;color:#6c63ff}}</style></head><body>
<h1>Digital Media Assistant — Report</h1><p style="color:#888">{now} | {an.get('category','').title()} | {an.get('sentiment','').title()}</p>
<h2>Main Event</h2><p>{an.get('main_event','')}</p>
<h2>Summary</h2><p>{an.get('detailed_summary_en','')}</p>
<h2>الملخص</h2><p dir="rtl">{an.get('detailed_summary_ar','')}</p>
<h2>Key Points</h2><ul>{kp}</ul>
<h2>Fake News Risk: {an.get('fake_news_risk_score',0):.0%}</h2><p>{an.get('fake_news_assessment_en','')}</p><ul>{fi}</ul>
<h2>Similarities</h2><ul>{sm or '<li>None</li>'}</ul>
<h2>Differences</h2><ul>{df or '<li>None</li>'}</ul>
<h2>Credibility: {cred.get('score',0)}/10</h2><div class="score-box"><div class="score-num">{cred.get('score',0)}/10</div><div>{cred.get('level_en','')}</div></div><ul>{cr}</ul>
<hr><p style="color:#888;font-size:.8rem">Generated by Digital Media Assistant</p></body></html>"""

# ── Session State (must be before sidebar) ──
for k in ["analysis","related_sources","related_analyses","comparison","credibility","export_posts","report_html","gen_article_en","gen_article_ar","chat_history","history","batch_results","timeline_data","monitored_topics","monitor_results"]:
    if k not in st.session_state: st.session_state[k]=[] if k in ("chat_history","history","batch_results","timeline_data","monitored_topics","monitor_results") else None

# ╔══════════════════════════════════════════════════════════════╗
# ║  SIDEBAR                                                    ║
# ╚══════════════════════════════════════════════════════════════╝
with st.sidebar:
    st.markdown('<div style="text-align:center;padding:1.2rem 0 .8rem"><div style="font-family:Playfair Display,serif;font-size:1.4rem;font-weight:800;background:linear-gradient(135deg,#6c63ff,#4da6ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent">◈ DMA</div><div style="color:var(--text-muted);font-size:.7rem;letter-spacing:2px;text-transform:uppercase;margin-top:3px">Settings</div></div>',unsafe_allow_html=True)
    st.markdown("---")
    interface_lang=st.selectbox("🌐 Language",["English","العربية"])
    is_ar=interface_lang=="العربية"
    theme_choice=st.selectbox("🎨 "+("المظهر" if is_ar else "Theme"),["🌙 Dark","☀️ Light"] if not is_ar else ["🌙 داكن","☀️ فاتح"])
    nt="dark" if ("Dark" in theme_choice or "داكن" in theme_choice) else "light"
    if nt!=st.session_state.theme: st.session_state.theme=nt; st.rerun()
    related_count=st.slider("🔍 "+("مصادر المقارنة" if is_ar else "Sources to compare"),1,5,3)
    deep_analysis=st.checkbox("🧠 "+("تحليل معمّق" if is_ar else "Deep analysis"),True)

    # ── Topic Monitoring Section ──
    st.markdown("---")
    st.markdown(f"**📡 {'مراقبة المواضيع' if is_ar else 'Topic Monitor'}**")

    new_topic=st.text_input("➕ "+("أضف موضوع" if is_ar else "Add topic"),placeholder="AI regulations" if not is_ar else "تنظيمات الذكاء الاصطناعي",key="new_topic_input",label_visibility="collapsed")
    if st.button("➕ "+("أضف" if is_ar else "Add"),key="add_topic_btn",use_container_width=True):
        if new_topic.strip() and new_topic.strip() not in [t["topic"] for t in st.session_state.monitored_topics]:
            st.session_state.monitored_topics.append({"topic":new_topic.strip(),"added":datetime.now().strftime("%m/%d %H:%M"),"alerts":[]})
            st.rerun()

    # Show monitored topics
    if st.session_state.monitored_topics:
        for i,t in enumerate(st.session_state.monitored_topics):
            alert_count=len(t.get("alerts",[]))
            tc1,tc2=st.columns([4,1])
            with tc1:
                badge=f' <span style="background:#ff4444;color:white;border-radius:10px;padding:1px 6px;font-size:.65rem;">{alert_count}</span>' if alert_count>0 else ""
                st.markdown(f'<div style="font-size:.82rem;color:var(--text-primary);padding:3px 0;">📡 {t["topic"]}{badge}</div>',unsafe_allow_html=True)
            with tc2:
                if st.button("✕",key=f"del_topic_{i}"):
                    st.session_state.monitored_topics.pop(i); st.rerun()

        if st.button("🔄 "+("مسح الآن" if is_ar else "Scan Now"),key="scan_topics",use_container_width=True):
            st.session_state._run_scan=True

    st.markdown("---")
    st.markdown("<p style='color:var(--text-muted);font-size:.7rem;text-align:center'>Powered by OpenAI</p>",unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════╗
# ║  MAIN UI                                                    ║
# ╚══════════════════════════════════════════════════════════════╝
st.markdown(f'<div class="hero-header"><div class="hero-title">Digital Media Assistant</div><div class="hero-subtitle">{"حلّل · قارن · تحقّق · انشر" if is_ar else "Analyze · Compare · Verify · Publish"}</div></div>',unsafe_allow_html=True)

input_mode=st.radio("",["🔗 "+("رابط" if is_ar else "URL"),"📝 "+("نص" if is_ar else "Text"),"🔄 "+("تحليل دفعي" if is_ar else "Batch")],horizontal=True,label_visibility="collapsed")
article_title=article_text=url_value=""
batch_urls_text=""
is_url="URL" in input_mode or "رابط" in input_mode
is_batch="Batch" in input_mode or "دفعي" in input_mode

if is_batch:
    st.info("🔄 "+("أدخل رابط في كل سطر (2-5 روابط)" if is_ar else "Enter one URL per line (2-5 URLs)"))
    batch_urls_text=st.text_area("الروابط" if is_ar else "URLs",height=150,placeholder="https://example.com/news-1\nhttps://example.com/news-2\nhttps://example.com/news-3")
elif is_url:
    url_value=st.text_input("أدخل الرابط" if is_ar else "Enter URL",placeholder="https://...")
else:
    article_title=st.text_input("عنوان" if is_ar else "Title (optional)")
    article_text=st.text_area("النص" if is_ar else "Paste text",height=220)

run=st.button("🚀 "+("حلّل" if is_ar else "Analyze"),type="primary",use_container_width=True)

# ╔══════════════════════════════════════════════════════════════╗
# ║  PIPELINE                                                   ║
# ╚══════════════════════════════════════════════════════════════╝

# ── Timeline Generator ──
def gen_timeline(analysis,related_analyses,related_sources):
    """Generate a timeline of events using LLM from all analyzed sources."""
    sys="You are a timeline reconstruction expert. Return valid JSON only."
    all_data={"primary":analysis,"related":[{"analysis":ra,"source":ra.get("_src",""),"url":ra.get("_url",""),"published":ra.get("_pub","")} for ra in related_analyses]}
    # Also include source metadata
    src_meta=[{"title":s.get("title",""),"source":s.get("source",""),"published":s.get("published",""),"link":s.get("link","")} for s in related_sources[:8]]
    usr=f"""Based on these news analyses and source metadata, reconstruct a chronological timeline of events.

Analyses: {json.dumps(all_data,ensure_ascii=False)[:8000]}

Source metadata: {json.dumps(src_meta,ensure_ascii=False)[:2000]}

Return JSON array of events sorted by date:
[{{"date":"YYYY-MM-DD or approximate","time":"HH:MM if known or empty","event_en":"What happened in English","event_ar":"ماذا حدث بالعربية","source":"Which source reported this","importance":"high/medium/low"}}]

Include at least 3-8 events. Use dates from the article text, published dates, or inferred chronological order.
If exact dates are unknown, use reasonable estimates and note them."""
    result=llm_json(sys,usr,0.15)
    if isinstance(result,dict) and "timeline" in result: return result["timeline"]
    if isinstance(result,list): return result
    return []

# ── Batch Pipeline ──
if run and is_batch:
    urls=[u.strip() for u in batch_urls_text.strip().split("\n") if u.strip().startswith("http")]
    if len(urls)<2: st.error("أدخل رابطين على الأقل" if is_ar else "Enter at least 2 URLs"); st.stop()
    if len(urls)>5: urls=urls[:5]; st.warning("تم تحديد 5 روابط كحد أقصى" if is_ar else "Limited to 5 URLs max")

    batch_results=[]
    progress=st.progress(0,text="🔄 "+("جارِ التحليل الدفعي..." if is_ar else "Batch analyzing..."))
    for idx,u in enumerate(urls):
        progress.progress((idx)/(len(urls)),text=f"📥 {idx+1}/{len(urls)}: {u[:50]}...")
        try:
            ext=extract_article(u)
            if ext.get("error") and not ext.get("text"):
                batch_results.append({"url":u,"error":ext["error"],"analysis":None})
                continue
            an=analyze_article(ext.get("title",""),ext.get("text",""))
            an["_url"]=u; an["_title"]=ext.get("title","")
            batch_results.append({"url":u,"error":"","analysis":an,"title":ext.get("title","")})
        except Exception as e:
            batch_results.append({"url":u,"error":str(e),"analysis":None})
        progress.progress((idx+1)/(len(urls)))

    st.session_state.batch_results=batch_results

    # Also save each to history
    for br in batch_results:
        if br.get("analysis"):
            a=br["analysis"]
            st.session_state.history.append({"time":datetime.now().strftime("%m/%d %H:%M"),"title":a.get("main_event",br.get("title",""))[:60],"cat":a.get("category","other"),"sent":a.get("sentiment","neutral"),"cred":0})

    progress.empty()
    st.success(f"✅ {len([b for b in batch_results if b.get('analysis')])} "+("خبر تم تحليله" if is_ar else "articles analyzed"))

# ── Single Article Pipeline ──
if run and not is_batch:
    if is_url:
        if not url_value.strip(): st.error("أدخل رابط" if is_ar else "Enter a URL"); st.stop()
        with st.spinner("📥 "+("استخراج..." if is_ar else "Extracting...")):
            ext=extract_article(url_value.strip())
        if ext.get("error") and not ext.get("text"): st.error(ext["error"]); st.stop()
        article_title=ext.get("title",""); article_text=ext.get("text",""); article_url=url_value.strip()
    else: article_url=""
    if not article_text.strip(): st.error("لا يوجد نص" if is_ar else "No text found"); st.stop()

    with st.spinner("🧠 "+("تحليل..." if is_ar else "Analyzing...")):
        analysis=analyze_article(article_title,article_text)
    st.session_state.analysis=analysis

    sq=analysis.get("search_query") or analysis.get("main_event") or article_title
    with st.spinner("🔍 "+("بحث..." if is_ar else "Searching...")):
        rsrc=search_sources(sq,related_count+4)
    st.session_state.related_sources=rsrc

    ra=[]
    if deep_analysis and rsrc:
        with st.spinner("📊 "+("تحليل المصادر..." if is_ar else "Analyzing sources...")):
            ra=deep_analyze_sources(rsrc,article_url,related_count)
    st.session_state.related_analyses=ra

    with st.spinner("⚖️ "+("مقارنة..." if is_ar else "Comparing...")):
        comp=compare_coverage(analysis,ra)
    st.session_state.comparison=comp

    fs=analysis.get("fake_news_risk_score",0.5)
    if not isinstance(fs,(int,float)): fs=0.5
    cred=build_credibility(article_url,len(ra),comp,fs)
    st.session_state.credibility=cred

    with st.spinner("✍️ "+("توليد محتوى..." if is_ar else "Generating...")):
        ep=gen_posts(analysis,comp)
    st.session_state.export_posts=ep
    st.session_state.report_html=gen_report_html(analysis,comp,cred,rsrc)
    st.session_state.chat_history=[]; st.session_state.gen_article_en=None; st.session_state.gen_article_ar=None

    st.session_state.history.append({"time":datetime.now().strftime("%m/%d %H:%M"),"title":analysis.get("main_event",article_title)[:60],"cat":analysis.get("category","other"),"sent":analysis.get("sentiment","neutral"),"cred":cred.get("score",0)})

    # Generate timeline
    with st.spinner("🕐 "+("بناء التايم لاين..." if is_ar else "Building timeline...")):
        tl=gen_timeline(analysis,ra,rsrc)
    st.session_state.timeline_data=tl

    st.success("✅ "+("تم!" if is_ar else "Done!"))

# ╔══════════════════════════════════════════════════════════════╗
# ║  RESULTS                                                    ║
# ╚══════════════════════════════════════════════════════════════╝
if st.session_state.analysis:
    an=st.session_state.analysis; comp=st.session_state.comparison or {}; cred=st.session_state.credibility or {}
    ep=st.session_state.export_posts or {}; rsrc=st.session_state.related_sources or []; ra=st.session_state.related_analyses or []

    tabs=st.tabs(["📋 "+("الملخص" if is_ar else "Summary"),"📊 "+("الداشبورد" if is_ar else "Dashboard"),"🕐 "+("التايم لاين" if is_ar else "Timeline"),"🔍 "+("كشف التضليل" if is_ar else "Fake Check"),"⚖️ "+("المقارنة" if is_ar else "Compare"),"🛡️ "+("المصداقية" if is_ar else "Credibility"),"🤖 "+("المحادثة" if is_ar else "Chat"),"📝 "+("مقال" if is_ar else "Article"),"📤 "+("تصدير" if is_ar else "Export")])

    # ── TAB 1: Summary ──
    with tabs[0]:
        cat=an.get("category","other").lower(); cc=CAT_COLORS.get(cat,"cat-default"); ci=CAT_ICONS.get(cat,"📰")
        st.markdown(f'<span class="category-badge {cc}">{ci} {cat.title()}</span> <span style="color:var(--text-muted);font-size:.8rem">({an.get("category_confidence",0):.0%})</span>',unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">{"الحدث" if is_ar else "Main Event"}</div>',unsafe_allow_html=True)
        st.markdown(f"**{an.get('main_event','')}**")
        c1,c2=st.columns(2)
        with c1: st.markdown('<div class="section-header">English Summary</div>',unsafe_allow_html=True); st.write(an.get("detailed_summary_en",""))
        with c2: st.markdown('<div class="section-header">الملخص العربي</div>',unsafe_allow_html=True); st.write(an.get("detailed_summary_ar",""))
        st.markdown(f'<div class="section-header">{"النقاط" if is_ar else "Key Points"}</div>',unsafe_allow_html=True)
        for p in an.get("key_points",[]): st.markdown(f"- {p}")
        st.markdown(f'<div class="section-header">{"الكيانات" if is_ar else "Entities"}</div>',unsafe_allow_html=True)
        e1,e2,e3,e4=st.columns(4)
        with e1:
            st.markdown(f"**{'أشخاص' if is_ar else 'People'}**")
            for x in an.get("prominent_people",[]): st.markdown(f'<span class="entity-tag">👤 {x}</span>',unsafe_allow_html=True)
        with e2:
            st.markdown(f"**{'منظمات' if is_ar else 'Organizations'}**")
            for x in an.get("organizations",[]): st.markdown(f'<span class="entity-tag">🏛️ {x}</span>',unsafe_allow_html=True)
        with e3:
            st.markdown(f"**{'مواقع' if is_ar else 'Locations'}**")
            for x in an.get("locations",[]): st.markdown(f'<span class="entity-tag">📍 {x}</span>',unsafe_allow_html=True)
        with e4:
            st.markdown(f"**{'تواريخ' if is_ar else 'Dates'}**")
            for x in an.get("dates",[]): st.markdown(f'<span class="entity-tag">📅 {x}</span>',unsafe_allow_html=True)

    # ── TAB 2: Dashboard ──
    with tabs[1]:
        st.markdown(f'<div class="section-header">{"لوحة المعلومات" if is_ar else "Dashboard"}</div>',unsafe_allow_html=True)
        d1,d2,d3,d4,d5=st.columns(5)
        ss=an.get("sentiment_score",0); ss=ss if isinstance(ss,(int,float)) else 0
        with d1: st.markdown(f'<div class="metric-card"><div class="metric-value">{an.get("sentiment","").title()}</div><div class="metric-label">{"المشاعر" if is_ar else "Sentiment"}</div></div>',unsafe_allow_html=True)
        with d2: st.markdown(f'<div class="metric-card"><div class="metric-value">{ss:+.2f}</div><div class="metric-label">{"الدرجة" if is_ar else "Score"}</div></div>',unsafe_allow_html=True)
        with d3: st.markdown(f'<div class="metric-card"><div class="metric-value">{an.get("media_tone","").title()}</div><div class="metric-label">{"النبرة" if is_ar else "Tone"}</div></div>',unsafe_allow_html=True)
        with d4: st.markdown(f'<div class="metric-card"><div class="metric-value">{ci} {cat.title()}</div><div class="metric-label">{"التصنيف" if is_ar else "Category"}</div></div>',unsafe_allow_html=True)
        with d5: st.markdown(f'<div class="metric-card"><div class="metric-value">{cred.get("score",0)}/10</div><div class="metric-label">{"المصداقية" if is_ar else "Credibility"}</div></div>',unsafe_allow_html=True)
        st.markdown("")
        r1,r2=st.columns(2)
        with r1: st.markdown(f"**{'تحليل المشاعر' if is_ar else 'Sentiment'}**"); st.info(an.get("sentiment_rationale_ar" if is_ar else "sentiment_rationale_en",""))
        with r2: st.markdown(f"**{'تحليل النبرة' if is_ar else 'Tone'}**"); st.info(an.get("media_tone_rationale_ar" if is_ar else "media_tone_rationale_en",""))
        bias=an.get("bias_indicators",[])
        if bias:
            st.markdown(f'<div class="section-header">{"التحيز" if is_ar else "Bias"}</div>',unsafe_allow_html=True)
            for b in bias: st.markdown(f"- ⚠️ {b}")
        kws=an.get("keywords",[])
        if kws:
            st.markdown(f'<div class="section-header">{"كلمات مفتاحية" if is_ar else "Keywords"}</div>',unsafe_allow_html=True)
            st.markdown(" ".join(f'<span class="entity-tag">🔑 {k}</span>' for k in kws),unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">{"إحصائيات" if is_ar else "Stats"}</div>',unsafe_allow_html=True)
        s1,s2,s3,s4=st.columns(4)
        with s1: st.metric("👤",len(an.get("prominent_people",[])))
        with s2: st.metric("🏛️",len(an.get("organizations",[])))
        with s3: st.metric("📍",len(an.get("locations",[])))
        with s4: st.metric("📅",len(an.get("dates",[])))

    # ── TAB 3: Timeline ──
    with tabs[2]:
        st.markdown(f'<div class="section-header">{"التسلسل الزمني للأحداث" if is_ar else "Event Timeline"}</div>',unsafe_allow_html=True)
        tl_data=st.session_state.timeline_data or []
        if tl_data and isinstance(tl_data,list):
            try: tl_data=sorted(tl_data,key=lambda x:x.get("date",""))
            except: pass

            for idx,ev in enumerate(tl_data):
                if not isinstance(ev,dict): continue
                imp=str(ev.get("importance","medium"))
                imp_icon={"high":"🔴","medium":"🟡","low":"🟢"}.get(imp,"🟡")
                ev_date=str(ev.get("date",""))
                ev_time=str(ev.get("time",""))
                ev_text=str(ev.get("event_ar" if is_ar else "event_en",""))
                ev_src=str(ev.get("source",""))

                # Use separate markdown calls to avoid f-string issues
                date_html=f'<div style="font-family:Playfair Display,serif;font-weight:700;font-size:0.95rem;color:var(--accent-primary);">{ev_date}</div><div style="font-size:0.75rem;color:var(--text-muted);">{ev_time}</div>'
                dot_color={"high":"#ff6b6b","medium":"#f5a623","low":"#2dd4a8"}.get(imp,"#f5a623")
                card_html=f'<div style="font-size:0.92rem;color:var(--text-primary);line-height:1.5;">{imp_icon} {ev_text}</div><div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.3rem;">📰 {ev_src}</div>'

                col_date,col_dot,col_card=st.columns([1.5,0.3,6])
                with col_date:
                    st.markdown(date_html,unsafe_allow_html=True)
                with col_dot:
                    st.markdown(f'<div style="width:14px;height:14px;border-radius:50%;background:{dot_color};margin:0 auto;margin-top:4px;"></div>',unsafe_allow_html=True)
                    if idx<len(tl_data)-1:
                        st.markdown('<div style="width:2px;height:40px;background:var(--border-color);margin:0 auto;"></div>',unsafe_allow_html=True)
                with col_card:
                    st.markdown(f'<div style="background:var(--bg-card);border:1px solid var(--border-color);border-left:3px solid {dot_color};border-radius:0 12px 12px 0;padding:1rem;">{card_html}</div>',unsafe_allow_html=True)

            st.markdown('<div style="margin-top:1.5rem;padding:0.8rem;background:var(--bg-secondary);border-radius:10px;display:flex;gap:1.5rem;justify-content:center;"><span style="font-size:0.8rem;color:var(--text-secondary);">🔴 High</span><span style="font-size:0.8rem;color:var(--text-secondary);">🟡 Medium</span><span style="font-size:0.8rem;color:var(--text-secondary);">🟢 Low</span></div>',unsafe_allow_html=True)
        else:
            st.info("🕐 "+("لا توجد بيانات كافية" if is_ar else "Not enough data for timeline"))

    # ── TAB 4: Fake News ──
    with tabs[3]:
        st.markdown(f'<div class="section-header">{"كشف التضليل" if is_ar else "Fake News Detection"}</div>',unsafe_allow_html=True)
        fs=an.get("fake_news_risk_score",0.5); fs=fs if isinstance(fs,(int,float)) else 0.5
        if fs>=0.7: ac,rle,rla,rc="fake-alert-high","HIGH RISK","خطر مرتفع","#ff4444"
        elif fs>=0.4: ac,rle,rla,rc="fake-alert-mid","MODERATE","متوسط","var(--accent-amber)"
        else: ac,rle,rla,rc="fake-alert-low","LOW RISK","منخفض","var(--accent-green)"
        st.markdown(f'<div class="fake-alert {ac}"><div class="fake-score" style="color:{rc}">{fs:.0%}</div><div style="font-weight:700;font-size:1.1rem;color:{rc};letter-spacing:1px">{rla if is_ar else rle}</div><p style="color:var(--text-secondary);margin-top:.8rem;font-size:.9rem">{an.get("fake_news_assessment_ar" if is_ar else "fake_news_assessment_en","")}</p></div>',unsafe_allow_html=True)
        inds=an.get("fake_news_indicators",[])
        if inds:
            st.markdown(f'<div class="section-header">{"المؤشرات" if is_ar else "Indicators"}</div>',unsafe_allow_html=True)
            for i in inds:
                if isinstance(i,dict):
                    sv=i.get("severity","medium"); si={"high":"🔴","medium":"🟡","low":"🟢"}.get(sv,"🟡")
                    st.markdown(f'<div class="fake-indicator">{si} [{sv.upper()}] {i.get("indicator","")}</div>',unsafe_allow_html=True)
        claims=an.get("factual_claims",[])
        if claims:
            st.markdown(f'<div class="section-header">{"ادعاءات قابلة للتحقق" if is_ar else "Verifiable Claims"}</div>',unsafe_allow_html=True)
            for idx,c in enumerate(claims,1): st.markdown(f"**{idx}.** {c}")
        miss=an.get("missing_context",[])
        if miss:
            st.markdown(f'<div class="section-header">{"سياق مفقود" if is_ar else "Missing Context"}</div>',unsafe_allow_html=True)
            for m in miss: st.markdown(f"- 🕳️ {m}")

    # ── TAB 4: Comparison ──
    with tabs[4]:
        st.markdown(f'<div class="section-header">{"المصادر" if is_ar else "Sources"}</div>',unsafe_allow_html=True)
        if rsrc:
            for idx,item in enumerate(rsrc[:related_count+2],1):
                st.markdown(f'<div class="source-card"><div class="source-title">{idx}. {item.get("title","")}</div><div class="source-meta">{item.get("source","")} · {item.get("published","")}</div></div>',unsafe_allow_html=True)
                if item.get("link"): st.link_button(f"{'افتح' if is_ar else 'Open'} {idx}",item["link"])
        if ra:
            for sk,si,sle,sla in [("similarities","✅","Similarities","التشابه"),("differences","🔸","Differences","الاختلافات"),("coverage_gaps","🕳️","Gaps","الفجوات")]:
                st.markdown(f'<div class="section-header">{sla if is_ar else sle}</div>',unsafe_allow_html=True)
                its=comp.get(sk,[])
                if its:
                    for i in its: st.markdown(f"- {si} {i}")
                else: st.info("لا يوجد" if is_ar else "None")
            st.markdown(f'<div class="section-header">{"ملخص" if is_ar else "Summary"}</div>',unsafe_allow_html=True)
            st.write(comp.get("comparison_summary_ar" if is_ar else "comparison_summary_en",""))

    # ── TAB 5: Credibility ──
    with tabs[5]:
        cs=cred.get("score",0); scl="cred-score-high" if cs>=8 else ("cred-score-mid" if cs>=5 else "cred-score-low")
        bc="#2dd4a8" if cs>=8 else ("#f5a623" if cs>=5 else "#ff6b6b")
        st.markdown(f'<div class="cred-gauge"><div class="cred-score {scl}">{cs}/10</div><div class="cred-label" style="color:{bc}">{cred.get("level_ar" if is_ar else "level_en","")}</div><div class="cred-bar"><div class="cred-bar-fill" style="width:{cs*10}%;background:{bc}"></div></div><p style="color:var(--text-muted);margin-top:10px;font-size:.85rem">{"النطاق" if is_ar else "Domain"}: <strong>{cred.get("domain","")}</strong></p></div>',unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">{"الأسباب" if is_ar else "Reasons"}</div>',unsafe_allow_html=True)
        for r in cred.get("reasons_ar" if is_ar else "reasons_en",[]): st.markdown(f"- {r}")
        st.markdown(f'<div class="section-header">{"المنهجية" if is_ar else "Method"}</div>',unsafe_allow_html=True)
        for idx,m in enumerate(cred.get("method_ar" if is_ar else "method_en",[]),1): st.markdown(f'<div class="method-step"><strong>{idx}.</strong> {m}</div>',unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">{"المراجع" if is_ar else "References"}</div>',unsafe_allow_html=True)
        for ref in cred.get("references",[]): st.markdown(f"- 📚 {ref}")

    # ── TAB 6: Chat ──
    with tabs[6]:
        st.markdown(f'<div class="section-header">{"محادثة ذكية" if is_ar else "Smart Chat"}</div>',unsafe_allow_html=True)
        st.caption("اسأل أي سؤال عن الخبر" if is_ar else "Ask anything about this article")
        for msg in st.session_state.chat_history:
            if msg["role"]=="user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])
        uq=st.chat_input("اكتب سؤالك..." if is_ar else "Your question...")
        if uq:
            st.session_state.chat_history.append({"role":"user","content":uq})
            ctx=json.dumps(an,ensure_ascii=False)[:8000]; cctx=json.dumps(comp,ensure_ascii=False)[:3000]
            sys_msg=f"You are a news analysis assistant. Answer based ONLY on this data. Reply in {'Arabic' if is_ar else 'English'}.\n\nAnalysis:\n{ctx}\n\nComparison:\n{cctx}"
            msgs=[{"role":"system","content":sys_msg}]+[{"role":m["role"],"content":m["content"]} for m in st.session_state.chat_history]
            with st.spinner("🤔..."): reply=llm_chat(msgs)
            st.session_state.chat_history.append({"role":"assistant","content":reply}); st.rerun()

    # ── TAB 7: Article Gen ──
    with tabs[7]:
        st.markdown(f'<div class="section-header">{"توليد مقال" if is_ar else "Generate Article"}</div>',unsafe_allow_html=True)
        gc1,gc2=st.columns(2)
        with gc1:
            if st.button("📝 English Article",use_container_width=True):
                with st.spinner("✍️..."): st.session_state.gen_article_en=gen_article(an,comp,"en"); st.rerun()
        with gc2:
            if st.button("📝 مقال عربي",use_container_width=True):
                with st.spinner("✍️..."): st.session_state.gen_article_ar=gen_article(an,comp,"ar"); st.rerun()
        if st.session_state.gen_article_en:
            st.markdown('<div class="section-header">English Article</div>',unsafe_allow_html=True)
            st.write(st.session_state.gen_article_en)
            st.download_button("💾 Save EN",st.session_state.gen_article_en.encode(),"article_en.txt","text/plain")
        if st.session_state.gen_article_ar:
            st.markdown('<div class="section-header">المقال العربي</div>',unsafe_allow_html=True)
            st.write(st.session_state.gen_article_ar)
            st.download_button("💾 حفظ AR",st.session_state.gen_article_ar.encode(),"article_ar.txt","text/plain",key="dl_ar_art")

    # ── TAB 8: Export ──
    with tabs[8]:
        st.markdown(f'<div class="section-header">{"تصدير" if is_ar else "Export"}</div>',unsafe_allow_html=True)
        def _surl(pk,t):
            e=quote_plus(t)
            if "telegram" in pk: return f"https://t.me/share/url?url=&text={e}"
            if "linkedin" in pk: return f"https://www.linkedin.com/sharing/share-offsite/?text={e}"
            if "x_post" in pk: return f"https://twitter.com/intent/tweet?text={e}"
            if "email" in pk: return f"mailto:?subject={quote_plus('News Update')}&body={e}"
            return ""
        def _slbl(pk):
            for k,v in {"telegram":"📱 Telegram","linkedin":"💼 LinkedIn","x_post":"🐦 X","email":"📧 Email"}.items():
                if k in pk: return v
            return ""
        def _ac(pk):
            for k,v in {"telegram":"#26A5E4","linkedin":"#0A66C2","x_post":"#f0eff4","instagram":"#E4405F","email":"#f5a623"}.items():
                if k in pk: return v
            return "#6c63ff"
        plats=[("📱 Telegram AR","telegram_ar"),("📱 Telegram EN","telegram_en"),("💼 LinkedIn EN","linkedin_en"),("💼 LinkedIn AR","linkedin_ar"),("🐦 X EN","x_post_en"),("🐦 X AR","x_post_ar"),("📸 Instagram EN","instagram_caption_en"),("📸 Instagram AR","instagram_caption_ar"),("📧 Email EN","email_newsletter_en"),("📧 Email AR","email_newsletter_ar")]
        ec1,ec2=st.columns(2)
        for idx,(lbl,key) in enumerate(plats):
            cnt=ep.get(key,""); col=ec1 if idx%2==0 else ec2; ac=_ac(key)
            with col:
                st.markdown(f'<div class="export-card" style="border-left:3px solid {ac}"><div class="export-platform" style="color:{ac}">{lbl}</div></div>',unsafe_allow_html=True)
                st.text_area(lbl,value=cnt,height=130,key=f"ex_{key}",label_visibility="collapsed")
                if cnt:
                    b1,b2,b3=st.columns(3)
                    with b1: st.download_button("📋 "+("نسخ" if is_ar else "Copy"),cnt.encode(),f"{key}.txt","text/plain",key=f"dl_{key}")
                    with b2:
                        su=_surl(key,cnt)
                        if su: st.link_button(_slbl(key),su)
                    with b3: st.download_button("💾",cnt.encode(),f"{key}.txt","text/plain",key=f"sv_{key}")
        st.markdown("---")
        rh=st.session_state.report_html
        if rh:
            st.download_button("📄 "+("تقرير HTML" if is_ar else "HTML Report"),rh.encode(),"dma_report.html","text/html",use_container_width=True)
            st.caption("💡 "+("افتح → طباعة → PDF" if is_ar else "Open → Print → Save as PDF"))

# ╔══════════════════════════════════════════════════════════════╗
# ║  BATCH RESULTS                                              ║
# ╚══════════════════════════════════════════════════════════════╝
if st.session_state.batch_results:
    st.markdown("---")
    st.markdown(f'<div class="section-header">🔄 {"نتائج التحليل الدفعي" if is_ar else "Batch Analysis Results"}</div>',unsafe_allow_html=True)

    # Summary metrics
    br=st.session_state.batch_results
    success=[b for b in br if b.get("analysis")]
    failed=[b for b in br if not b.get("analysis")]

    bm1,bm2,bm3=st.columns(3)
    with bm1: st.markdown(f'<div class="metric-card"><div class="metric-value">{len(br)}</div><div class="metric-label">{"إجمالي" if is_ar else "Total"}</div></div>',unsafe_allow_html=True)
    with bm2: st.markdown(f'<div class="metric-card"><div class="metric-value">{len(success)}</div><div class="metric-label">{"ناجح" if is_ar else "Success"}</div></div>',unsafe_allow_html=True)
    with bm3: st.markdown(f'<div class="metric-card"><div class="metric-value">{len(failed)}</div><div class="metric-label">{"فشل" if is_ar else "Failed"}</div></div>',unsafe_allow_html=True)

    st.markdown("")

    # Comparison table across batch articles
    if len(success)>=2:
        st.markdown(f'<div class="section-header">{"مقارنة سريعة بين الأخبار" if is_ar else "Quick Comparison"}</div>',unsafe_allow_html=True)
        for idx,b in enumerate(success,1):
            a=b["analysis"]
            cat_b=a.get("category","other").lower()
            ci_b=CAT_ICONS.get(cat_b,"📰")
            sent=a.get("sentiment","neutral")
            sent_icon={"positive":"🟢","negative":"🔴","neutral":"🔵"}.get(sent,"🔵")
            fs_b=a.get("fake_news_risk_score",0.5)
            fs_b=fs_b if isinstance(fs_b,(int,float)) else 0.5
            tone=a.get("media_tone","")

            st.markdown(f"""
            <div class="source-card" style="border-left-color:var(--accent-{'green' if sent=='positive' else ('secondary' if sent=='negative' else 'blue')})">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
                    <div>
                        <div class="source-title">{idx}. {a.get('main_event','')[:80]}</div>
                        <div class="source-meta">{b.get('url','')[:60]}...</div>
                    </div>
                    <div style="display:flex;gap:0.8rem;align-items:center;">
                        <span class="entity-tag">{ci_b} {cat_b.title()}</span>
                        <span class="entity-tag">{sent_icon} {sent.title()}</span>
                        <span class="entity-tag">🎭 {tone.title()}</span>
                        <span class="entity-tag">⚠️ {fs_b:.0%}</span>
                    </div>
                </div>
            </div>""",unsafe_allow_html=True)

    # Expandable details for each article
    st.markdown(f'<div class="section-header">{"تفاصيل كل خبر" if is_ar else "Article Details"}</div>',unsafe_allow_html=True)
    for idx,b in enumerate(success,1):
        a=b["analysis"]
        with st.expander(f"📰 {idx}. {a.get('main_event','')[:70]}"):
            dc1,dc2=st.columns(2)
            with dc1:
                st.markdown("**English Summary**")
                st.write(a.get("detailed_summary_en",""))
            with dc2:
                st.markdown("**الملخص العربي**")
                st.write(a.get("detailed_summary_ar",""))

            st.markdown("**Key Points:**")
            for p in a.get("key_points",[]): st.markdown(f"- {p}")

            mt1,mt2,mt3,mt4=st.columns(4)
            with mt1: st.metric("Sentiment",a.get("sentiment","").title())
            with mt2: st.metric("Tone",a.get("media_tone","").title())
            with mt3: st.metric("Category",a.get("category","").title())
            with mt4:
                fss=a.get("fake_news_risk_score",0)
                fss=fss if isinstance(fss,(int,float)) else 0
                st.metric("Fake Risk",f"{fss:.0%}")

    # Failed articles
    if failed:
        st.markdown(f'<div class="section-header">{"أخبار فشل تحليلها" if is_ar else "Failed Articles"}</div>',unsafe_allow_html=True)
        for b in failed:
            st.error(f"❌ {b.get('url','')[:60]} — {b.get('error','Unknown error')}")

# ╔══════════════════════════════════════════════════════════════╗
# ║  TOPIC MONITORING — SCAN & RESULTS                          ║
# ╚══════════════════════════════════════════════════════════════╝

def scan_topic(topic_query,max_results=5):
    """Scan Google News RSS for a topic and analyze each result briefly."""
    sources=search_sources(topic_query,limit=max_results)
    results=[]
    for s in sources:
        # Quick LLM analysis of the RSS snippet
        snippet=s.get("summary","") or s.get("title","")
        if snippet:
            try:
                quick=llm_json("You are a news classifier. Return JSON only.",
                    f"""Classify this news headline/snippet:
Title: {s.get('title','')}
Snippet: {snippet}

Return JSON: {{"relevance":"high/medium/low","sentiment":"positive/negative/neutral","urgency":"breaking/important/normal","one_line_ar":"ملخص سطر واحد بالعربية","one_line_en":"One line English summary"}}""",0.15)
            except:
                quick={"relevance":"medium","sentiment":"neutral","urgency":"normal","one_line_ar":s.get("title",""),"one_line_en":s.get("title","")}
        else:
            quick={"relevance":"low","sentiment":"neutral","urgency":"normal","one_line_ar":"","one_line_en":""}

        results.append({**s,**quick,"scanned_at":datetime.now().strftime("%H:%M")})
    return results

# Run scan if triggered from sidebar
if getattr(st.session_state,"_run_scan",False):
    st.session_state._run_scan=False
    if st.session_state.monitored_topics:
        scan_progress=st.progress(0,text="📡 "+("جارِ مسح المواضيع..." if is_ar else "Scanning topics..."))
        all_results=[]
        for tidx,t in enumerate(st.session_state.monitored_topics):
            scan_progress.progress((tidx)/(len(st.session_state.monitored_topics)),text=f"📡 {t['topic']}...")
            try:
                results=scan_topic(t["topic"],max_results=4)
                # Filter high relevance as alerts
                alerts=[r for r in results if r.get("relevance") in ("high","medium")]
                st.session_state.monitored_topics[tidx]["alerts"]=alerts
                st.session_state.monitored_topics[tidx]["last_scan"]=datetime.now().strftime("%m/%d %H:%M")
                all_results.append({"topic":t["topic"],"results":results,"alerts":alerts})
            except Exception as e:
                all_results.append({"topic":t["topic"],"results":[],"alerts":[],"error":str(e)})
            scan_progress.progress((tidx+1)/(len(st.session_state.monitored_topics)))
        st.session_state.monitor_results=all_results
        scan_progress.empty()
        total_alerts=sum(len(r.get("alerts",[])) for r in all_results)
        st.success(f"📡 {'تم المسح!' if is_ar else 'Scan complete!'} — {total_alerts} {'تنبيه' if is_ar else 'alerts'}")

# Display monitoring results
if st.session_state.monitor_results:
    st.markdown("---")
    st.markdown(f'<div class="section-header">📡 {"نتائج مراقبة المواضيع" if is_ar else "Topic Monitoring Results"}</div>',unsafe_allow_html=True)

    for mr in st.session_state.monitor_results:
        topic=mr.get("topic","")
        results=mr.get("results",[])
        alerts=mr.get("alerts",[])

        alert_badge=f' <span style="background:#ff4444;color:white;border-radius:10px;padding:2px 8px;font-size:.75rem;font-weight:600;">{len(alerts)} {"تنبيه" if is_ar else "alerts"}</span>' if alerts else ""

        st.markdown(f'<div class="section-header" style="font-size:1.2rem;">📡 {topic}{alert_badge}</div>',unsafe_allow_html=True)

        if not results:
            st.info("لم يتم العثور على نتائج" if is_ar else "No results found")
            continue

        for ridx,r in enumerate(results):
            rel=r.get("relevance","low")
            urg=r.get("urgency","normal")
            sent=r.get("sentiment","neutral")

            rel_icon={"high":"🔴","medium":"🟡","low":"🟢"}.get(rel,"🟢")
            urg_icon={"breaking":"🚨","important":"⚡","normal":"📰"}.get(urg,"📰")
            sent_icon={"positive":"🟢","negative":"🔴","neutral":"🔵"}.get(sent,"🔵")

            border_color="var(--accent-secondary)" if urg=="breaking" else ("var(--accent-amber)" if urg=="important" else "var(--accent-primary)")

            st.markdown(f"""
            <div class="source-card" style="border-left-color:{border_color};">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem;">
                    <div style="flex:1;">
                        <div class="source-title">{urg_icon} {r.get('title','')}</div>
                        <div style="color:var(--text-secondary);font-size:.88rem;margin:.4rem 0;">
                            {r.get('one_line_ar' if is_ar else 'one_line_en','')}
                        </div>
                        <div class="source-meta">{r.get('source','')} · {r.get('published','')} · {"مسح" if is_ar else "Scanned"}: {r.get('scanned_at','')}</div>
                    </div>
                    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
                        <span class="entity-tag">{rel_icon} {rel.title()}</span>
                        <span class="entity-tag">{sent_icon} {sent.title()}</span>
                    </div>
                </div>
            </div>""",unsafe_allow_html=True)

            if r.get("link"):
                st.link_button(f"{'افتح' if is_ar else 'Open'} →",r["link"],key=f"mon_{topic}_{ridx}")

        st.markdown("")

# ── History in Sidebar ──
if st.session_state.history:
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**📂 {'السجل' if is_ar else 'History'}** ({len(st.session_state.history)})")
        for h in reversed(st.session_state.history[-10:]):
            ci2=CAT_ICONS.get(h.get("cat",""),"📰")
            st.markdown(f'<div style="font-size:.78rem;color:var(--text-secondary);padding:4px 0;border-bottom:1px solid var(--border-color)">{ci2} {h["title"]}...<br><span style="font-size:.68rem">{h["time"]} · {h["sent"]} · {h["cred"]}/10</span></div>',unsafe_allow_html=True)
