import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.core.config import settings


def _get_llm(temperature: float = 0.7) -> ChatGroq:
    """
    Build a ChatGroq client. Model name and API key always come from settings
    (.env), per project requirements -- never hardcoded.
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,# type: ignore[arg-type]
        model=settings.LLM_MODEL,
        temperature=temperature,
    )


# ---------------------------------------------------------------------------
# Task 1: single combined call
# ---------------------------------------------------------------------------

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert content writer and SEO copywriter. "
            "You write engaging, well-structured blog articles.",
        ),
        (
            "human",
            """Write a complete blog article about the topic below.

Topic: {topic}
Tone: {tone}

Respond EXACTLY in this format (no extra commentary, no markdown code fences):

TITLE: <a catchy article title>
OUTLINE:
- <point 1>
- <point 2>
- <point 3>
- <point 4>
ARTICLE:
<the full article, at least 400 words, written in markdown, matching the requested tone>
""",
        ),
    ]
)


def _parse_llm_output(raw_text: str) -> dict:
    """Parse the single LLM response into title / outline / article."""
    title_match = re.search(r"TITLE:\s*(.+)", raw_text)
    outline_match = re.search(r"OUTLINE:\s*(.*?)ARTICLE:", raw_text, re.DOTALL)
    article_match = re.search(r"ARTICLE:\s*(.*)", raw_text, re.DOTALL)

    title = title_match.group(1).strip() if title_match else "Untitled Article"
    outline = outline_match.group(1).strip() if outline_match else ""
    article = article_match.group(1).strip() if article_match else raw_text.strip()

    return {"title": title, "outline": outline, "article": article}


async def generate_article_content(topic: str, tone: str) -> dict:
    """
    Generate title + outline + full article in a SINGLE LLM call. Kept from Task 1.
    """
    llm = _get_llm()
    chain = _PROMPT | llm | StrOutputParser()

    raw_output = await chain.ainvoke({"topic": topic, "tone": tone})
    return _parse_llm_output(raw_output)


# ---------------------------------------------------------------------------
# Task 2: granular steps used by the Celery chain
# ---------------------------------------------------------------------------

_TITLE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an expert blog editor who writes catchy, click-worthy titles."),
        (
            "human",
            "Generate ONE catchy blog title for the topic below. "
            "Respond with ONLY the title text, nothing else, no quotes.\n\n"
            "Topic: {topic}\nTone: {tone}",
        ),
    ]
)

_OUTLINE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert content strategist who writes clear, well-structured "
            "article outlines.",
        ),
        (
            "human",
            "Create a bullet-point outline (4-6 points) for a blog article.\n\n"
            "Title: {title}\nTopic: {topic}\nTone: {tone}\n\n"
            "Respond with ONLY the bullet points, one per line, each starting with '-'.",
        ),
    ]
)

_ARTICLE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an expert content writer and SEO copywriter."),
        (
            "human",
            "Write the full blog article in markdown, at least 400 words, matching "
            "the requested tone, following the outline closely.\n\n"
            "Title: {title}\nTopic: {topic}\nTone: {tone}\nOutline:\n{outline}\n\n"
            "Respond with ONLY the article body (no title heading repetition needed).",
        ),
    ]
)


async def generate_title(topic: str, tone: str) -> str:
    llm = _get_llm()
    chain = _TITLE_PROMPT | llm | StrOutputParser()
    result = await chain.ainvoke({"topic": topic, "tone": tone})
    return result.strip().strip('"')


async def generate_outline(topic: str, tone: str, title: str) -> str:
    llm = _get_llm()
    chain = _OUTLINE_PROMPT | llm | StrOutputParser()
    result = await chain.ainvoke({"topic": topic, "tone": tone, "title": title})
    return result.strip()


async def generate_full_article(topic: str, tone: str, title: str, outline: str) -> str:
    llm = _get_llm()
    chain = _ARTICLE_PROMPT | llm | StrOutputParser()
    result = await chain.ainvoke({"topic": topic, "tone": tone, "title": title, "outline": outline})
    return result.strip()


# ---------------------------------------------------------------------------
# Task 3: on-demand newsletter summary (used by POST /generate-newsletter/{id})
# ---------------------------------------------------------------------------

_NEWSLETTER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You write punchy, concise email newsletter blurbs that drive clicks.",
        ),
        (
            "human",
            "Summarize this article into a short newsletter blurb (3-5 sentences) "
            "that entices readers to click through and read the full article. "
            "Respond with ONLY the blurb.\n\nTitle: {title}\nArticle:\n{article}",
        ),
    ]
)


async def generate_newsletter_summary(title: str, article: str) -> str:
    llm = _get_llm(temperature=0.5)
    chain = _NEWSLETTER_PROMPT | llm | StrOutputParser()
    result = await chain.ainvoke({"title": title, "article": article[:3000]})
    return result.strip()
