"""
services/news_service.py
-------------------------
Fetches recent financial news headlines for a ticker via NewsAPI.org.
NEWS_API_KEY is optional — if absent or blank the service returns an
empty list and the AI prompt notes that no news data was available.

NewsAPI free tier: 100 requests/day, articles from last 30 days.
NewsAPI developer tier: no rate limit, 1 month history.

Error handling philosophy:
    News is enrichment data, not critical path. Any network failure,
    rate-limit, or missing API key produces an empty list + a log warning.
    The AI pipeline continues and generates the report without news context.

Rate-limit note:
    We request max 10 articles to keep prompt tokens low.
    The sentiment service will score each headline.
"""

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 8.0       # seconds before we give up on the news API


@dataclass
class RawArticle:
    title: str
    source: str
    published_at: str       # ISO-8601 string from API
    description: str | None = None


def fetch_news(ticker: str, company_name: str | None = None) -> list[RawArticle]:
    """
    Fetch up to 10 recent English-language news articles about `ticker`.

    Uses `company_name` to broaden the search if available:
        e.g.  "NVDA OR NVIDIA" gives better coverage than "NVDA" alone.

    Returns an empty list (never raises) on any error.
    """
    ticker_upper = ticker.strip().upper()
    if not settings.NEWS_API_KEY:
        logger.warning(
            "news.fetch ticker=%s provider=newsapi status=skipped reason=missing_api_key",
            ticker_upper,
        )
        return []

    # Build query string: ticker + optional company name
    query_parts = [ticker_upper]
    if company_name:
        # Use first word of company name to avoid too-narrow results
        short_name = company_name.split()[0]
        if short_name.upper() != ticker.upper():
            query_parts.append(short_name)

    query = " OR ".join(query_parts)

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": settings.NEWS_API_KEY,
    }

    try:
        logger.info(
            "news.fetch ticker=%s provider=newsapi request_query=%s",
            ticker_upper,
            query,
        )
        response = httpx.get(
            f"{settings.NEWS_API_BASE_URL}/everything",
            params=params,
            timeout=_TIMEOUT,
        )
        logger.info(
            "news.fetch ticker=%s provider=newsapi response_status=%s",
            ticker_upper,
            response.status_code,
        )
        response.raise_for_status()
        data = response.json()

        articles: list[RawArticle] = []
        for item in data.get("articles", []):
            title = (item.get("title") or "").strip()
            if not title or title == "[Removed]":
                continue

            articles.append(
                RawArticle(
                    title=title,
                    source=item.get("source", {}).get("name", "Unknown"),
                    published_at=item.get("publishedAt", "")[:10],   # keep date only
                    description=item.get("description"),
                )
            )

        preview_titles = [a.title for a in articles[:3]]
        logger.info(
            "news.fetch ticker=%s provider=newsapi articles_returned=%d first_3_titles=%s",
            ticker_upper,
            len(articles),
            preview_titles,
        )
        return articles

    except httpx.TimeoutException:
        logger.warning("news.fetch ticker=%s provider=newsapi status=timeout", ticker_upper)
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "news.fetch ticker=%s provider=newsapi status=http_error response_status=%s error=%s",
            ticker_upper,
            exc.response.status_code,
            exc,
        )
    except Exception as exc:
        logger.error(
            "news.fetch ticker=%s provider=newsapi status=error error=%s",
            ticker_upper,
            exc,
            exc_info=True,
        )

    return []
