import time

import requests
import streamlit as st

API_BASE = "http://api:8000"

st.set_page_config(
    page_title="AI Content Automation",
    page_icon="🤖",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def api_get(path: str) -> dict | list | None:
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach API. Make sure the backend is running.")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_post(path: str, payload: dict | None = None) -> dict | None:
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload or {}, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach API. Make sure the backend is running.")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

PAGES = [
    "📊 Dashboard",
    "🏷️ Topics",
    "⚡ Generate Article",
    "📝 Articles",
    "📧 Newsletters",
    "🔍 Task Monitor",
]

st.sidebar.title("🤖 AI Content Platform")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption("AI Blog + Newsletter Automation")

# ---------------------------------------------------------------------------
# Page: Dashboard
# ---------------------------------------------------------------------------

if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    st.markdown("System overview — live data from the backend.")

    topics     = api_get("/topics")      or []
    articles   = api_get("/articles")    or []
    newsletters= api_get("/newsletters") or []
    stats      = api_get("/tasks/stats") or {}

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Topics",      len(topics))
    col2.metric("Total Articles",    len(articles))
    col3.metric("Total Newsletters", len(newsletters))
    col4.metric("Active Tasks",      stats.get("active", 0))
    col5.metric("Failed Tasks",      stats.get("failed", 0))

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Recent Articles")
        if articles:
            for a in articles[:5]:
                icon = "🟢" if a["status"] == "COMPLETED" else "🔴" if a["status"] == "FAILED" else "🟡"
                st.markdown(f"{icon} **{a['title'] or 'Untitled'}** — `{a['status']}`")
        else:
            st.info("No articles yet.")

    with col_b:
        st.subheader("Recent Newsletters")
        if newsletters:
            for n in newsletters[:5]:
                st.markdown(f"📧 Newsletter #{n['id']} → Article #{n['article_id']}")
        else:
            st.info("No newsletters yet.")

    if st.button("🔄 Refresh"):
        st.rerun()

# ---------------------------------------------------------------------------
# Page: Topics
# ---------------------------------------------------------------------------

elif page == "🏷️ Topics":
    st.title("🏷️ Topics")
    st.subheader("Create a new topic")

    with st.form("create_topic_form"):
        name = st.text_input("Topic name", placeholder="e.g. Benefits of Remote Work")
        tone = st.selectbox("Tone", ["professional", "friendly", "casual", "neutral", "persuasive"])
        submitted = st.form_submit_button("Create Topic")

    if submitted:
        if not name.strip():
            st.warning("Topic name cannot be empty.")
        else:
            result = api_post("/topics", {"name": name.strip(), "tone": tone})
            if result:
                st.success(f"✅ Topic created — ID: {result['id']}")

    st.markdown("---")
    st.subheader("All Topics")

    topics = api_get("/topics") or []
    if topics:
        for t in topics:
            with st.expander(f"#{t['id']} — {t['name']} ({t['tone']})"):
                st.write(f"**ID:** {t['id']}")
                st.write(f"**Name:** {t['name']}")
                st.write(f"**Tone:** {t['tone']}")
                st.write(f"**Created:** {t['created_at']}")
    else:
        st.info("No topics yet. Create one above.")

# ---------------------------------------------------------------------------
# Page: Generate Article
# ---------------------------------------------------------------------------

elif page == "⚡ Generate Article":
    st.title("⚡ Generate Article")

    topics = api_get("/topics") or []

    if not topics:
        st.warning("No topics found. Create a topic first.")
    else:
        topic_map = {f"#{t['id']} — {t['name']} ({t['tone']})": t["id"] for t in topics}
        selected_label = st.selectbox("Select a topic", list(topic_map.keys()))
        selected_id = topic_map[selected_label]

        if st.button("🚀 Generate Article"):
            with st.spinner("Queuing article generation..."):
                result = api_post(f"/generate/{selected_id}")

            if result:
                task_id = result.get("task_id")
                st.success(f"✅ Queued! Task ID: `{task_id}`")
                st.markdown("---")
                st.subheader("Polling task status...")

                status_placeholder = st.empty()

                for i in range(30):
                    task = api_get(f"/tasks/{task_id}")
                    if not task:
                        break

                    state = task.get("state", "UNKNOWN")
                    status_placeholder.info(f"**State:** `{state}` (poll {i + 1}/30)")

                    if state == "SUCCESS":
                        status_placeholder.success(f"✅ Done! State: `{state}`")
                        res = task.get("result", {})
                        st.write(f"**Article ID:** {res.get('article_id')}")
                        st.write(f"**Title:** {res.get('title')}")
                        st.write(f"**Status:** {res.get('status')}")
                        break
                    elif state == "FAILURE":
                        status_placeholder.error(f"❌ Failed: {task.get('result')}")
                        break

                    time.sleep(3)
                else:
                    status_placeholder.warning("⏳ Timed out. Check Task Monitor for the result.")

# ---------------------------------------------------------------------------
# Page: Articles
# ---------------------------------------------------------------------------

elif page == "📝 Articles":
    st.title("📝 Articles")

    articles = api_get("/articles") or []

    if not articles:
        st.info("No articles yet. Generate one from the Generate Article page.")
    else:
        st.markdown(f"**{len(articles)} article(s) found.**")
        st.markdown("---")

        for a in articles:
            icon = "🟢" if a["status"] == "COMPLETED" else "🔴" if a["status"] == "FAILED" else "🟡"
            label = f"{icon} #{a['id']} — {a['title'] or 'Untitled'} [{a['status']}]"
            with st.expander(label):
                col1, col2 = st.columns(2)
                col1.write(f"**Article ID:** {a['id']}")
                col1.write(f"**Topic ID:** {a['topic_id']}")
                col2.write(f"**Status:** `{a['status']}`")
                col2.write(f"**Created:** {a['created_at']}")
                if a.get("content"):
                    st.markdown("---")
                    st.markdown(a["content"])
                else:
                    st.info("Content not available yet.")

    if st.button("🔄 Refresh"):
        st.rerun()

# ---------------------------------------------------------------------------
# Page: Newsletters
# ---------------------------------------------------------------------------

elif page == "📧 Newsletters":
    st.title("📧 Newsletters")

    col_left, col_right = st.columns([2, 1])

    with col_right:
        st.subheader("Generate Newsletter")
        articles = api_get("/articles") or []
        completed = [a for a in articles if a["status"] == "COMPLETED"]

        if not completed:
            st.info("No completed articles yet.")
        else:
            article_map = {f"#{a['id']} — {a['title'] or 'Untitled'}": a["id"] for a in completed}
            selected_label = st.selectbox("Select article", list(article_map.keys()))
            selected_article_id = article_map[selected_label]

            if st.button("📧 Generate Newsletter"):
                with st.spinner("Generating newsletter..."):
                    result = api_post(f"/generate-newsletter/{selected_article_id}")
                if result:
                    st.success(f"✅ Newsletter #{result['newsletter_id']} created!")
                    st.rerun()

    with col_left:
        st.subheader("All Newsletters")
        newsletters = api_get("/newsletters") or []

        if not newsletters:
            st.info("No newsletters yet.")
        else:
            for n in newsletters:
                with st.expander(f"📧 Newsletter #{n['id']} → Article #{n['article_id']}"):
                    st.write(f"**Newsletter ID:** {n['id']}")
                    st.write(f"**Article ID:** {n['article_id']}")
                    st.write(f"**Created:** {n['created_at']}")
                    st.markdown("---")
                    st.write(n["content"])

        if st.button("🔄 Refresh"):
            st.rerun()

# ---------------------------------------------------------------------------
# Page: Task Monitor
# ---------------------------------------------------------------------------

elif page == "🔍 Task Monitor":
    st.title("🔍 Task Monitor")

    task_id_input = st.text_input(
        "Enter Task ID", placeholder="e.g. 3f2a1b4c-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    )

    if st.button("Check Status"):
        if not task_id_input.strip():
            st.warning("Please enter a task ID.")
        else:
            task = api_get(f"/tasks/{task_id_input.strip()}")
            if task:
                state = task.get("state", "UNKNOWN")
                if state == "SUCCESS":
                    st.success(f"✅ State: `{state}`")
                elif state == "FAILURE":
                    st.error(f"❌ State: `{state}`")
                else:
                    st.info(f"⏳ State: `{state}`")

                result = task.get("result")
                if result:
                    st.markdown("**Result:**")
                    st.json(result)

    st.markdown("---")
    st.subheader("Task Stats")

    stats = api_get("/tasks/stats") or {}
    col1, col2, col3 = st.columns(3)
    col1.metric("Active",    stats.get("active", 0))
    col2.metric("Scheduled", stats.get("scheduled", 0))
    col3.metric("Failed",    stats.get("failed", 0))

    if st.button("🔄 Refresh Stats"):
        st.rerun()