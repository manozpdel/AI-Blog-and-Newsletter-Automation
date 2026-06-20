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
        api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        temperature=temperature,
    )


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
    Generate title + outline + full article in a SINGLE LLM call
    using LangChain's Groq integration (no multi-step pipeline yet).

    Returns:
        {"title": str, "outline": str, "article": str}
    """
    llm = _get_llm()
    chain = _PROMPT | llm | StrOutputParser()

    raw_output = await chain.ainvoke({"topic": topic, "tone": tone})
    return _parse_llm_output(raw_output)