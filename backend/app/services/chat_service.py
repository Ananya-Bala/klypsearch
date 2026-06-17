"""
services/chat_service.py
-------------------------
Research Assistant chatbot service.

Handles multi-stock, multi-topic research questions by:
    1. Extracting ticker symbols from the natural language query
    2. Fetching live market data for each ticker (reusing market_data_service)
    3. Fetching news and computing sentiment for each ticker (reusing existing services)
    4. Querying ChromaDB for relevant earnings filing context
    5. Building a rich multi-company prompt
    6. Calling Groq for a synthesized research answer
    7. Returning a structured ChatResponse

Design principles:
    - Reuses ALL existing services (market_data, news, sentiment, document)
    - Never touches /research/analyze or analysis_service
    - Fails gracefully per-ticker: if NVDA data fetch fails, AMD still gets analyzed
    - Groq is called once regardless of how many tickers are in the query
    - Total prompt stays under ~4000 tokens via concise per-ticker blocks
"""

import logging
import re
from datetime import datetime, timezone

from groq import APIError as GroqAPIError
from groq import Groq

from app.core.config import settings
from app.schemas.chat import ChatResponse, DocumentSource, TickerSentiment
from app.services.document_service import format_document_context, search_documents
from app.services.market_data_service import MarketSnapshot, currency_symbol, fetch_market_data
from app.services.news_service import fetch_news
from app.services.sentiment_service import analyze_news_sentiment

logger = logging.getLogger(__name__)


class ChatError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ── Ticker extraction ─────────────────────────────────────────────────────────

# Common company name → ticker mapping for natural language resolution
_NAME_TO_TICKER: dict[str, str] = {
    "nvidia":    "NVDA",
    "nvda":      "NVDA",
    "apple":     "AAPL",
    "aapl":      "AAPL",
    "microsoft": "MSFT",
    "msft":      "MSFT",
    "tesla":     "TSLA",
    "tsla":      "TSLA",
    "amazon":    "AMZN",
    "amzn":      "AMZN",
    "amd":       "AMD",
    "advanced micro": "AMD",
    "google":    "GOOG",
    "alphabet":  "GOOG",
    "goog":      "GOOG",
    "googl":     "GOOGL",
    "meta":      "META",
    "facebook":  "META",
    "netflix":   "NFLX",
    "nflx":      "NFLX",
    "intel":     "INTC",
    "intc":      "INTC",
    "salesforce":"CRM",
    "crm":       "CRM",
    "palantir":  "PLTR",
    "pltr":      "PLTR",
    "snowflake": "SNOW",
    "snow":      "SNOW",
    "broadcom":  "AVGO",
    "avgo":      "AVGO",
    "qualcomm":  "QCOM",
    "qcom":      "QCOM",
    "tsmc":      "TSM",
    "tsm":       "TSM",
    "arm":       "ARM",
    "shopify":   "SHOP",
    "shop":      "SHOP",
    "uber":      "UBER",
    "lyft":      "LYFT",
    "airbnb":    "ABNB",
    "abnb":      "ABNB",
    "coinbase":  "COIN",
    "coin":      "COIN",
    "spotify":   "SPOT",
    "spot":      "SPOT",

    # Banks / financials (common natural-language queries)
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "goldman": "GS",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
}

# Regex for bare uppercase tickers (2–5 uppercase letters, word-bounded)
_TICKER_RE = re.compile(r"\b([A-Z]{2,5})\b")

# Yahoo Finance ticker-like token validator (supports suffixes like .NS).
# Examples: JPM, GS, MSFT, TCS.NS, RELIANCE.NS
_YF_TICKER_RE = re.compile(r"[A-Z]{1,10}(?:\.[A-Z]{1,5})?")

# Extraction patterns:
# - Strict uppercase tokens (avoids matching normal words like "Compare")
_YF_TICKER_EXTRACT_UPPER_RE = re.compile(
    r"(?<![A-Za-z0-9])([A-Z]{1,10}(?:\.[A-Z]{1,5})?)(?![A-Za-z0-9])"
)
# - Suffix tokens like tcs.ns (case-insensitive, but requires a dot suffix)
_YF_TICKER_EXTRACT_SUFFIX_RE = re.compile(
    r"(?<![A-Za-z0-9])([A-Za-z]{1,10}\.[A-Za-z]{1,5})(?![A-Za-z0-9])"
)

# Stop-words that look like tickers but aren't
_TICKER_STOPWORDS = {
    "AI", "IT", "US", "AND", "OR", "THE", "FOR", "ARE", "NOT", "BUT",
    "CEO", "CFO", "EPS", "GDP", "ETF", "IPO", "P/E", "YOY", "QOQ",
    "RSI", "SMA", "ATH", "ROI", "FCF", "TTM", "PE", "VS", "AS", "IF",
    "IN", "OF", "ON", "TO", "BY", "AT", "AN", "A",
}


def _is_valid_ticker_token(token: str) -> bool:
    """
    Lightweight validation for a ticker-like token.
    We intentionally do NOT check against any hardcoded list or the document KB.
    Market-data lookup should be the source of truth.
    """
    if not token:
        return False
    t = token.upper().strip()
    if t in _TICKER_STOPWORDS:
        return False
    return bool(_YF_TICKER_RE.fullmatch(t))


def extract_tickers(query: str, max_tickers: int = 4) -> list[str]:
    """
    Extract stock ticker symbols from a natural language query.

    Strategy:
    1. Scan for known company names (case-insensitive)
    2. Scan for bare uppercase ticker patterns (2–5 caps letters)
    3. Deduplicate and return in order of first appearance

    Returns a list of uppercase ticker strings, max `max_tickers` items.
    """
    found: list[str] = []
    seen: set[str]   = set()
    text_lower = query.lower()

    # Step 1: company name lookup
    # Sort by length descending so "advanced micro" matches before "micro"
    for name, ticker in sorted(_NAME_TO_TICKER.items(), key=lambda x: -len(x[0])):
        if name in text_lower and ticker not in seen:
            found.append(ticker)
            seen.add(ticker)
            if len(found) >= max_tickers:
                break

    # Step 2: ticker-like token scan (supports suffixes like .NS)
    # Prefer strict uppercase tokens, then allow dot-suffix tokens in any case.
    if len(found) < max_tickers:
        for match in _YF_TICKER_EXTRACT_UPPER_RE.finditer(query):
            t = match.group(1).upper()
            if _is_valid_ticker_token(t) and t not in seen:
                found.append(t)
                seen.add(t)
                if len(found) >= max_tickers:
                    break
    if len(found) < max_tickers:
        for match in _YF_TICKER_EXTRACT_SUFFIX_RE.finditer(query):
            t = match.group(1).upper()
            if _is_valid_ticker_token(t) and t not in seen:
                found.append(t)
                seen.add(t)
                if len(found) >= max_tickers:
                    break

    logger.info("Extracted %d ticker(s) from query %r: %s", len(found), query[:60], found)
    return found[:max_tickers]


# ── Per-ticker data fetch ─────────────────────────────────────────────────────

def _fmt(v, suffix: str = "", p: int = 2) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, float):
        return f"{v:.{p}f}{suffix}"
    return f"{v}{suffix}"


def _pct(v: float | None) -> str:
    if v is None:
        return "N/A"
    return f"{v * 100:.1f}%"


def _fetch_ticker_context(ticker: str) -> dict:
    """
    Fetch market data + news + sentiment for a single ticker.
    Returns a dict with snapshot + sentiment, or None fields on error.
    """
    snap: MarketSnapshot | None = None
    sentiment_label  = "neutral"
    sentiment_score  = 0.0
    news_headlines: list[str] = []

    try:
        snap = fetch_market_data(ticker)
        logger.info(
            "chat.market_data_fetch ticker=%s ok=true company_name=%r current_price=%r",
            ticker,
            getattr(snap, "company_name", None),
            getattr(snap, "current_price", None),
        )
    except Exception as exc:
        logger.warning("Market data failed for %s: %s", ticker, exc)
        logger.info("chat.market_data_fetch ticker=%s ok=false error=%r", ticker, str(exc))

    try:
        articles = fetch_news(ticker, snap.company_name if snap else None)
        sent     = analyze_news_sentiment(articles)
        sentiment_label = sent.overall_label
        sentiment_score = sent.overall_score
        news_headlines  = [a.title for a in sent.articles[:3]]
    except Exception as exc:
        logger.warning("News/sentiment failed for %s: %s", ticker, exc)

    return {
        "ticker":           ticker,
        "snap":             snap,
        "sentiment_label":  sentiment_label,
        "sentiment_score":  sentiment_score,
        "news_headlines":   news_headlines,
    }


def _build_ticker_block(ctx: dict) -> str:
    """Format a single ticker's data into a concise prompt block."""
    t    = ctx["ticker"]
    snap = ctx["snap"]

    if snap is None:
        return f"=== {t} ===\nNo market data available.\n"

    sym = currency_symbol(getattr(snap, "currency", None))
    return f"""=== {t} — {snap.company_name or 'Unknown'} ===
Price: {_fmt(snap.current_price, sym)}  |  Market Cap: {_fmt(snap.market_cap)}
P/E: {_fmt(snap.pe_ratio, 'x')}  |  Forward P/E: {_fmt(snap.forward_pe, 'x')}  |  EPS: {_fmt(snap.eps, sym)}
Revenue Growth: {_pct(snap.revenue_growth)}  |  Profit Margin: {_pct(snap.profit_margins)}
Debt/Equity: {_fmt(snap.debt_to_equity)}  |  FCF: {_fmt(snap.free_cash_flow)}
Analyst: {snap.strong_buy + snap.buy} Buy / {snap.hold} Hold / {snap.sell + snap.strong_sell} Sell  |  Mean Target: {_fmt(snap.mean_target_price, sym)}
RSI (14): {_fmt(snap.rsi, '')}  |  SMA50: {_fmt(snap.sma_50, sym)}  |  SMA200: {_fmt(snap.sma_200, sym)}
Golden Cross: {snap.golden_cross}  |  Volume Trend: {snap.volume_trend or 'N/A'}
News Sentiment: {ctx['sentiment_label'].upper()} ({ctx['sentiment_score']:+.2f})
Recent Headlines: {'; '.join(ctx['news_headlines']) or 'None available'}"""


# ── Groq call ─────────────────────────────────────────────────────────────────

def _build_chat_system_prompt() -> str:
    return """You are a senior institutional equity research analyst specializing in comparative analysis.

Your role is to answer research questions by synthesizing data across multiple companies.

RULES:
1. Ground every claim in the data provided. Do not invent numbers.
2. When comparing companies, be specific: name which metric favors which company and by how much.
3. Separate short-term (0–3 months) from long-term (6–12 months) outlook when relevant.
4. If fundamental strength and technical signals conflict, explain why.
5. If risk-adjusted returns differ significantly (Sharpe, volatility), highlight the implication.
6. Cite earnings filing context when relevant — it adds credibility.
7. Use probabilistic language: "suggests", "indicates", "likely", not "will" or "certain".
8. End with a clear, actionable conclusion: preferred position, entry conditions, or key watchpoints.
9. Write in flowing paragraphs, not bullet lists. Aim for 300–600 words.
10. Never start with "Based on the data" or "As an AI". Start with the substance."""


def _build_chat_user_prompt(
    query: str,
    ticker_contexts: list[dict],
    doc_context: str,
) -> str:
    ticker_blocks = "\n\n".join(_build_ticker_block(ctx) for ctx in ticker_contexts)
    tickers_str   = ", ".join(ctx["ticker"] for ctx in ticker_contexts)

    return f"""Answer this research question: "{query}"

Analyze the following companies: {tickers_str}

{ticker_blocks}

{doc_context}

=== INSTRUCTIONS ===
Synthesize the data above to answer the question directly and specifically.
Compare the companies where relevant. Cite document context if it strengthens the analysis.
Conclude with an actionable research view."""


# ── Main entry point ──────────────────────────────────────────────────────────

def answer_research_query(query: str, max_tickers: int = 4) -> ChatResponse:
    """
    Full chatbot pipeline:
        1. Extract tickers from query
        2. Fetch market data + sentiment per ticker (parallel-ish via list comprehension)
        3. Query ChromaDB for relevant document context
        4. Build prompt and call Groq
        5. Return structured ChatResponse

    Raises ChatError on unrecoverable failures (no tickers found, Groq down).
    """
    if not settings.GROQ_API_KEY:
        raise ChatError("GROQ_API_KEY is not configured.", status_code=503)

    # ── Step 1: Extract + validate tickers ────────────────────────────────────
    logger.info("chat.ticker_debug raw_query=%r", query)
    extracted = extract_tickers(query, max_tickers=max_tickers)
    validated: list[str] = []
    rejected: list[str] = []
    seen: set[str] = set()
    for t in extracted:
        if t in seen:
            continue
        seen.add(t)
        if _is_valid_ticker_token(t):
            validated.append(t)
        else:
            rejected.append(t)

    logger.info(
        "chat.ticker_debug extracted_tickers=%s validated_tickers=%s rejected_tickers=%s",
        extracted,
        validated,
        rejected,
    )

    if not validated:
        raise ChatError(
            "No stock tickers or company names detected in your query. "
            "Try including a ticker symbol like NVDA, AAPL, or MSFT.",
            status_code=422,
        )

    # ── Step 2: Fetch data per ticker ─────────────────────────────────────────
    logger.info("[chat] Fetching data for %d ticker(s): %s", len(validated), validated)
    ticker_contexts = [_fetch_ticker_context(t) for t in validated]

    # ── Step 3: Document retrieval ────────────────────────────────────────────
    logger.info("[chat] Querying ChromaDB for: %r", query[:80])
    doc_chunks = search_documents(query, n_results=4)

    # Also pull ticker-specific chunks
    for t in validated[:2]:  # limit to avoid overloading prompt
        extra = search_documents(f"{t} earnings revenue growth", ticker=t, n_results=2)
        for chunk in extra:
            if chunk not in doc_chunks:
                doc_chunks.append(chunk)

    # Deduplicate by text and cap at 5
    seen_texts: set[str] = set()
    unique_chunks = []
    for chunk in doc_chunks:
        key = chunk["text"][:100]
        if key not in seen_texts:
            seen_texts.add(key)
            unique_chunks.append(chunk)
        if len(unique_chunks) >= 5:
            break

    doc_context = format_document_context(unique_chunks[:5])
    logger.info("[chat] Using %d document chunk(s) as context", len(unique_chunks))

    # ── Step 4: Build prompt and call Groq ────────────────────────────────────
    system_prompt = _build_chat_system_prompt()
    user_prompt   = _build_chat_user_prompt(query, ticker_contexts, doc_context)

    logger.info("[chat] Calling Groq %s (prompt ~%d chars)", settings.GROQ_MODEL, len(user_prompt))

    try:
        client   = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=1200,
        )
    except GroqAPIError as exc:
        raise ChatError(f"Groq API error: {exc}", status_code=502)

    answer            = response.choices[0].message.content or "No response generated."
    prompt_tokens     = response.usage.prompt_tokens     if response.usage else 0
    completion_tokens = response.usage.completion_tokens if response.usage else 0

    logger.info("[chat] Answer generated (%d+%d tokens)", prompt_tokens, completion_tokens)

    # ── Step 5: Assemble response ─────────────────────────────────────────────
    ticker_details = []
    for ctx in ticker_contexts:
        snap = ctx["snap"]
        ticker_details.append(TickerSentiment(
            ticker=ctx["ticker"],
            company_name=snap.company_name if snap else None,
            current_price=snap.current_price if snap else None,
            currency=getattr(snap, "currency", None) if snap else None,
            sentiment=ctx["sentiment_label"],
            sentiment_score=ctx["sentiment_score"],
            recommendation=None,   # analyst rec not fetched in chat mode for speed
        ))

    doc_sources = [
        DocumentSource(
            company=ch["company"],
            source=ch["source"],
            score=ch["score"],
            text_preview=ch["text"][:200],
        )
        for ch in unique_chunks
    ]

    return ChatResponse(
        query=query,
        answer=answer,
        tickers_analyzed=validated,
        ticker_details=ticker_details,
        document_sources=doc_sources,
        generated_at=datetime.now(timezone.utc),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
