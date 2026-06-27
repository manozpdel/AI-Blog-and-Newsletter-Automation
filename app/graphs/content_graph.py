import re
from typing import TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from app.core.config import settings


class ContentState(TypedDict):
    topic: str
    tone: str
    keywords: str
    title: str
    outline: str
    article: str
    seo_meta: str
    newsletter: str


def _get_llm(temperature: float = 0.7) -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        temperature=temperature,
    )


def _parse_title_outline(raw: str) -> tuple[str, str]:
    title_match = re.search(r"TITLE:\s*(.+)", raw)
    outline_match = re.search(r"OUTLINE:\s*(.*)", raw, re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Untitled Article"
    outline = outline_match.group(1).strip() if outline_match else ""
    return title, outline


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


async def keyword_node(state: ContentState) -> dict:
    llm = _get_llm(temperature=0.3)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an SEO keyword researcher."),
            (
                "human",
                "List 5-8 comma-separated SEO keywords for this topic. "
                "Respond with ONLY the comma-separated list, nothing else.\n\n"
                "Topic: {topic}",
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    keywords = await chain.ainvoke({"topic": state["topic"]})
    return {"keywords": keywords.strip()}


async def outline_node(state: ContentState) -> dict:
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert content strategist."),
            (
                "human",
                "Create a catchy title and a 4-6 point bullet outline for a blog "
                "article.\n\nTopic: {topic}\nTone: {tone}\nTarget keywords: {keywords}\n\n"
                "Respond EXACTLY as:\nTITLE: <title>\nOUTLINE:\n- point\n- point",
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    raw = await chain.ainvoke(
        {"topic": state["topic"], "tone": state["tone"], "keywords": state["keywords"]}
    )
    title, outline = _parse_title_outline(raw)
    return {"title": title, "outline": outline}


async def article_node(state: ContentState) -> dict:
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert blog writer and copywriter."),
            (
                "human",
                "Write the full blog article in markdown, at least 400 words, "
                "matching the tone, naturally weaving in the target keywords.\n\n"
                "Title: {title}\nTopic: {topic}\nTone: {tone}\n"
                "Outline:\n{outline}\nKeywords: {keywords}\n\n"
                "Respond with ONLY the article body.",
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    article = await chain.ainvoke(
        {
            "title": state["title"],
            "topic": state["topic"],
            "tone": state["tone"],
            "outline": state["outline"],
            "keywords": state["keywords"],
        }
    )
    return {"article": article.strip()}


async def seo_node(state: ContentState) -> dict:
    llm = _get_llm(temperature=0.3)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an SEO specialist."),
            (
                "human",
                "Write a single SEO meta description (max 160 characters) for this "
                "article. Respond with ONLY the meta description.\n\n"
                "Title: {title}\nArticle:\n{article}",
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    seo_meta = await chain.ainvoke({"title": state["title"], "article": state["article"][:2000]})
    return {"seo_meta": seo_meta.strip()}


async def newsletter_node(state: ContentState) -> dict:
    llm = _get_llm(temperature=0.5)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You write punchy, concise email newsletter blurbs that drive clicks."),
            (
                "human",
                "Summarize this article into a short newsletter blurb (3-5 sentences) "
                "that entices readers to click through and read the full article.\n\n"
                "Title: {title}\nArticle:\n{article}",
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    newsletter = await chain.ainvoke(
        {"title": state["title"], "article": state["article"][:2000]}
    )
    return {"newsletter": newsletter.strip()}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------


def build_content_graph():
    graph = StateGraph(ContentState)

    graph.add_node("keyword", keyword_node)
    graph.add_node("outline", outline_node)
    graph.add_node("article", article_node)
    graph.add_node("seo", seo_node)
    graph.add_node("newsletter", newsletter_node)

    graph.set_entry_point("keyword")
    graph.add_edge("keyword", "outline")
    graph.add_edge("outline", "article")
    graph.add_edge("article", "seo")
    graph.add_edge("seo", "newsletter")
    graph.add_edge("newsletter", END)

    return graph.compile()


_compiled_graph = build_content_graph()


async def run_content_pipeline(topic: str, tone: str) -> ContentState:
    """
    Run the full LangGraph pipeline: keywords -> outline -> article -> SEO -> newsletter.
    Used by the Celery Beat daily automation job.
    """
    initial_state: ContentState = {
        "topic": topic,
        "tone": tone,
        "keywords": "",
        "title": "",
        "outline": "",
        "article": "",
        "seo_meta": "",
        "newsletter": "",
    }
    result = await _compiled_graph.ainvoke(initial_state)
    return result