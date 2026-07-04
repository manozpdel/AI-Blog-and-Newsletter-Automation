# AI Content Automation Platform

A production-style, end-to-end AI content generation and newsletter delivery platform built with FastAPI, LangGraph, LangChain, Celery, and Docker.

The platform automates the full content lifecycle: it generates SEO-optimised blog articles using a multi-step LangGraph pipeline powered by Groq LLMs, summarises them into newsletter blurbs, delivers those newsletters to a managed subscriber list over SMTP, and exposes the entire system through a clean HTML/CSS admin dashboard — all orchestrated by Celery background workers and Celery Beat scheduling.

This project was built as a portfolio-grade demonstration of modern Python backend engineering: asynchronous FastAPI, event-driven task processing with RabbitMQ, structured logging, Redis caching, and a modular, testable architecture that follows an MVC-like separation of concerns.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Screenshots](#screenshots)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [Docker Services](#docker-services)
- [API Documentation](#api-documentation)
- [Celery Workflow](#celery-workflow)
- [LangGraph Workflow](#langgraph-workflow)
- [Email Automation](#email-automation)
- [Monitoring](#monitoring)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Feature | Description |
|---|---|
| AI Article Generation | Multi-step LangGraph pipeline generating title, outline, full article, and SEO metadata |
| Newsletter Generation | Automatic summarisation of articles into email-ready newsletter blurbs |
| LangGraph Workflow | Five-node directed graph: Keywords → Outline → Article → SEO → Newsletter |
| Celery Background Tasks | Non-blocking article and email delivery tasks with chaining and retry logic |
| RabbitMQ Message Broker | Dedicated `content_queue` and `email_queue` for task routing |
| Redis Caching | 24-hour deduplication cache preventing regeneration of the same topic on the same day |
| PostgreSQL | Persistent storage for topics, articles, newsletters, subscribers, and email logs |
| SMTP Email Delivery | HTML email delivery via Gmail SMTP with Jinja2 templated emails |
| Subscriber Management | Full CRUD, CSV bulk import, active/inactive toggle |
| HTML Admin Dashboard | Server-rendered Bootstrap 5 dashboard served directly from FastAPI |
| Task Monitoring | Live task lookup, email delivery log, 5-second auto-refresh |
| Flower Monitoring | Real-time Celery worker and queue visibility |
| Celery Beat Scheduling | Daily automated content and newsletter generation at 06:00 UTC |
| Dockerised Deployment | Single `docker compose up --build` starts all seven services |

---

## Tech Stack

| Technology | Purpose | Version |
|---|---|---|
| Python | Primary language | 3.11 |
| FastAPI | REST API and HTML page serving | 0.115+ |
| Jinja2 | Server-side HTML templating | 3.1+ |
| Bootstrap 5 | Dashboard UI framework | 5.3 |
| SQLAlchemy | Async ORM | 2.0+ |
| asyncpg | Async PostgreSQL driver | 0.29+ |
| psycopg2-binary | Sync PostgreSQL driver (Celery tasks) | 2.9+ |
| PostgreSQL | Relational database | 16 |
| Redis | Result backend and dedup cache | 7 |
| RabbitMQ | Celery message broker | 3 |
| Celery | Distributed task queue | 5.3+ |
| Celery Beat | Scheduled task runner | — |
| Flower | Celery real-time monitoring | 2.0+ |
| LangChain | LLM integration layer | 0.3+ |
| LangGraph | Stateful LLM workflow orchestration | 0.2+ |
| langchain-groq | Groq LLM provider for LangChain | 0.2+ |
| Groq | Inference API (LLaMA 3.3 70B) | — |
| smtplib | Standard library SMTP email delivery | — |
| Jinja2 | HTML email templating | 3.1+ |
| pydantic-settings | Environment variable management | 2.3+ |
| uv | Fast Python package manager | latest |
| Docker | Containerisation | — |
| Docker Compose | Multi-service orchestration | — |

---

## Architecture

```mermaid
graph TD
    Browser["Browser"]
    FastAPI["FastAPI\n(api:8000)"]
    Templates["Jinja2 Templates\nHTML Dashboard"]
    PG["PostgreSQL"]
    Redis["Redis\nCache + Result Backend"]
    RMQ["RabbitMQ\nMessage Broker"]
    Worker["Celery Worker\ncontent_queue + email_queue"]
    Beat["Celery Beat\nScheduler"]
    Flower["Flower\nMonitoring :5555"]
    LG["LangGraph\nPipeline"]
    Groq["Groq API\nLLaMA 3.3 70B"]
    SMTP["Gmail SMTP"]
    Subs["Subscribers"]

    Browser -->|"HTTP"| FastAPI
    FastAPI -->|"Render"| Templates
    FastAPI -->|"Read/Write"| PG
    FastAPI -->|"Cache"| Redis
    FastAPI -->|"Enqueue Task"| RMQ
    Beat -->|"Scheduled Jobs"| RMQ
    RMQ -->|"Consume"| Worker
    Worker -->|"Run Pipeline"| LG
    LG -->|"LLM Calls"| Groq
    Worker -->|"Write Results"| PG
    Worker -->|"Send Email"| SMTP
    SMTP -->|"Deliver"| Subs
    Flower -->|"Inspect"| Worker
```

---

## Screenshots

### Dashboard
![Dashboard](docs/images/dashboard.png)

---

### Topics
![Topics](docs/images/topics.png)

---

### Articles
![Articles](docs/images/articles.png)

---

### Newsletters
![Newsletters](docs/images/newsletters.png)

---

### Subscribers
![Subscribers](docs/images/subscribers.png)

---

### Task Monitor
![Task Monitor](docs/images/task-monitor.png)

---

### Flower Dashboard
![Flower](docs/images/flower.png)

---

## Project Structure

```
ai-blog-newsletter-platform/
├── app/
│   ├── api/
│   │   ├── page_routes.py        # HTML page routes (Jinja2)
│   │   └── routes.py             # REST API endpoints
│   ├── core/
│   │   ├── config.py             # Pydantic settings (env vars)
│   │   ├── logging.py            # Structured request logging middleware
│   │   └── rate_limit.py         # Redis-based rate limiting (100 req/min)
│   ├── db/
│   │   ├── base.py               # SQLAlchemy declarative base
│   │   └── session.py            # Async (FastAPI) + sync (Celery) engines
│   ├── graphs/
│   │   └── content_graph.py      # LangGraph 5-node content pipeline
│   ├── models/
│   │   ├── models.py             # Topic, Article ORM models
│   │   ├── newsletter.py         # Newsletter ORM model
│   │   ├── subscriber.py         # Subscriber ORM model
│   │   └── email_log.py          # EmailLog ORM model
│   ├── schemas/
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   └── subscriber.py         # Subscriber + email schemas
│   ├── services/
│   │   ├── llm_service.py        # LangChain + Groq LLM functions
│   │   ├── email_service.py      # SMTP send + Jinja2 template renderer
│   │   └── cache_service.py      # Redis dedup cache (topic + date)
│   ├── tasks/
│   │   ├── content_tasks.py      # Celery article generation chain
│   │   ├── scheduled_tasks.py    # Celery Beat daily job
│   │   └── email_tasks.py        # Email dispatch + retry tasks
│   ├── templates/
│   │   ├── base.html             # Master layout
│   │   ├── dashboard.html
│   │   ├── topics.html
│   │   ├── generate.html
│   │   ├── articles.html
│   │   ├── newsletters.html
│   │   ├── subscribers.html
│   │   ├── task_monitor.html
│   │   ├── email.html            # Jinja2 HTML email template
│   │   └── components/
│   │       ├── navbar.html
│   │       ├── sidebar.html
│   │       └── footer.html
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/app.js
│   ├── workers/
│   │   └── celery_app.py         # Celery app, queues, Beat schedule
│   └── main.py                   # FastAPI app, middleware, routing
├── docs/
│   └── images/                   # Screenshot placeholders
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Installation

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended)
- [uv](https://github.com/astral-sh/uv) for local development without Docker
- A [Groq API key](https://console.groq.com)
- A Gmail account with a [Google App Password](https://myaccount.google.com/apppasswords)

### Clone the repository

```bash
git clone https://github.com/your-username/ai-blog-newsletter-platform.git
cd ai-blog-newsletter-platform
```

### Install dependencies (local development)

```bash
uv sync
```

---

## Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@postgres:5432/ai_content_db` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `GROQ_API_KEY` | API key from [console.groq.com](https://console.groq.com) | `gsk_...` |
| `LLM_MODEL` | Groq model name | `llama-3.3-70b-versatile` |
| `CELERY_BROKER_URL` | RabbitMQ AMQP URL | `amqp://guest:guest@rabbitmq:5672//` |
| `CELERY_RESULT_BACKEND` | Redis URL for Celery results | `redis://redis:6379/0` |
| `EMAIL_PROVIDER` | Email transport (always `smtp`) | `smtp` |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USE_TLS` | Enable STARTTLS | `true` |
| `SMTP_USERNAME` | Gmail address | `you@gmail.com` |
| `SMTP_PASSWORD` | 16-character Google App Password | `abcdefghijklmnop` |
| `EMAIL_FROM` | Sender address (must match `SMTP_USERNAME` for Gmail) | `you@gmail.com` |
| `EMAIL_BATCH_SIZE` | Max emails queued per dispatch | `50` |
| `EMAIL_MAX_RETRIES` | Celery retry attempts per email | `5` |

> **Gmail setup:** enable 2-Step Verification on your Google account, then generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords). Use the 16-character password (no spaces) as `SMTP_PASSWORD`. Never use your normal Gmail password.

---

## Running the Project

### With Docker (recommended)

```bash
docker compose up --build
```

All services start automatically. Tables are created on first boot.

### Local development (without Docker)

Ensure PostgreSQL and Redis are running locally and update `.env` to use `localhost` instead of Docker service names.

```bash
uv sync
uv run uvicorn app.main:app --reload
```

### Access points

| URL | Description |
|---|---|
| `http://localhost:8000` | HTML Dashboard |
| `http://localhost:8000/api/docs` | Swagger UI (REST API) |
| `http://localhost:5555` | Flower (Celery monitor) |
| `http://localhost:15672` | RabbitMQ Management UI (`guest` / `guest`) |

---

## Docker Services

| Service | Container | Port | Description |
|---|---|---|---|
| `api` | `ai-content-api` | 8000 | FastAPI application — REST API + HTML dashboard |
| `worker` | `ai-content-worker` | — | Celery worker consuming `content_queue` and `email_queue` |
| `beat` | `ai-content-beat` | — | Celery Beat scheduler — triggers daily content generation at 06:00 UTC |
| `flower` | `ai-content-flower` | 5555 | Real-time Celery task monitoring UI |
| `postgres` | `ai-content-postgres` | 5432 | PostgreSQL 16 database |
| `redis` | `ai-content-redis` | 6379 | Redis — Celery result backend and dedup cache |
| `rabbitmq` | `ai-content-rabbitmq` | 5672 / 15672 | RabbitMQ message broker with management UI |

---

## API Documentation

Full interactive documentation is available at `http://localhost:8000/api/docs`.

### Topics

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/topics` | Create a topic |
| `GET` | `/topics` | List all topics |
| `PUT` | `/topics/{id}` | Update a topic |
| `DELETE` | `/topics/{id}` | Delete a topic |

### Articles

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate/{topic_id}` | Queue article generation (returns `task_id`) |
| `GET` | `/articles` | List all articles |
| `GET` | `/articles/{id}` | Get a single article |

### Newsletters

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate-newsletter/{article_id}` | Generate newsletter + queue email delivery |
| `GET` | `/newsletters` | List all newsletters |
| `GET` | `/newsletters/{id}` | Get a single newsletter |

### Subscribers

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/subscribers` | Add a subscriber |
| `GET` | `/subscribers` | List all subscribers |
| `GET` | `/subscribers/{id}` | Get a subscriber |
| `PUT` | `/subscribers/{id}` | Update a subscriber |
| `DELETE` | `/subscribers/{id}` | Delete a subscriber |
| `POST` | `/subscribers/import` | Bulk import from CSV (`name,email` header) |

### Email

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/email/logs` | All email delivery logs |
| `GET` | `/email/logs/{newsletter_id}` | Logs for a specific newsletter |
| `GET` | `/email/statistics` | Aggregate delivery stats |
| `POST` | `/email/retry/{newsletter_id}` | Re-queue all failed emails for a newsletter |

### Tasks & Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/tasks/{task_id}` | Get Celery task state and result |
| `GET` | `/tasks/stats` | Active, scheduled, and reserved task counts |
| `GET` | `/health` | Service health check |

---

## Celery Workflow

Article generation and email delivery are fully asynchronous. The API returns a `task_id` immediately; the work happens in the background.

```mermaid
flowchart TD
    A["POST /generate/{topic_id}"] --> B["Create Article row\nstatus: PENDING"]
    B --> C["Dispatch Celery chain\ncontent_queue"]
    C --> D["generate_title_task"]
    D --> E["generate_outline_task"]
    E --> F["generate_article_task\nstatus: COMPLETED"]
    F --> G["POST /generate-newsletter/{article_id}"]
    G --> H["Save Newsletter"]
    H --> I["dispatch_newsletter_emails\nemail_queue"]
    I --> J["send_newsletter_to_subscriber\n× 1 task per subscriber"]
    J -->|"Success"| K["EmailLog: SENT"]
    J -->|"Failure"| L["Retry × 5\nexponential backoff"]
    L -->|"Max retries exceeded"| M["EmailLog: FAILED"]
```

### Queue routing

| Queue | Tasks |
|---|---|
| `content_queue` | `generate_title_task`, `generate_outline_task`, `generate_article_task`, `daily_content_generation` |
| `email_queue` | `dispatch_newsletter_emails`, `send_newsletter_to_subscriber`, `retry_failed_emails` |

---

## LangGraph Workflow

Article generation is orchestrated by a LangGraph `StateGraph`. Each node makes a single LLM call to Groq; state is passed between nodes via a typed `ContentState` dict.

```mermaid
flowchart LR
    START(["Start"]) --> KW["KeywordNode\nExtract 5-8 SEO keywords"]
    KW --> OL["OutlineNode\nGenerate title + 4-6 point outline"]
    OL --> AR["ArticleNode\nWrite full article (400+ words)"]
    AR --> SE["SEONode\nWrite meta description (≤160 chars)"]
    SE --> NL["NewsletterNode\nWrite 3-5 sentence email blurb"]
    NL --> END(["End"])
```

| Node | Input | Output |
|---|---|---|
| `KeywordNode` | topic, tone | keywords |
| `OutlineNode` | topic, tone, keywords | title, outline |
| `ArticleNode` | topic, tone, title, outline, keywords | article |
| `SEONode` | title, article | seo_meta |
| `NewsletterNode` | title, article | newsletter blurb |

---

## Email Automation

### Transport

Emails are sent via Gmail SMTP using Python's built-in `smtplib` with STARTTLS. No third-party email SDK is required.

### Delivery flow

1. A newsletter is saved to the database.
2. `dispatch_newsletter_emails` fetches all active subscribers and queues one `send_newsletter_to_subscriber` Celery task per subscriber into `email_queue`.
3. Each task renders the Jinja2 HTML email template and sends it over SMTP.
4. Every attempt is recorded in the `EmailLog` table with status `SENT`, `FAILED`, `PENDING`, or `RETRYING`.

### Retry strategy

```python
@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
```

Failed sends are retried up to 5 times with exponential backoff. After all retries are exhausted, the `EmailLog` record is set to `FAILED` and can be re-queued via `POST /email/retry/{newsletter_id}`.

### Subscriber management

- Add individual subscribers via the dashboard or `POST /subscribers`
- Bulk import via CSV upload (`name,email` header row)
- Toggle active/inactive per subscriber — inactive subscribers are skipped during dispatch

---

## Monitoring

### Flower

Real-time Celery monitoring is available at `http://localhost:5555`. Flower displays active workers, queue depths, task states, execution times, and retry counts.

### Task Monitor page

The built-in Task Monitor page at `http://localhost:8000/tasks/page` polls `/tasks/stats` and `/email/logs` every 5 seconds and allows manual task lookup by ID.

### Health endpoint

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### Structured logging

Every HTTP request is assigned a unique `request_id` and logged with method, path, status code, and execution time in milliseconds. The `X-Request-ID` header is returned on every response.

```
[ef34a5d4] → POST /generate/1
[ef34a5d4] ← 200 (POST /generate/1) 12.4ms
```

### Rate limiting

A Redis-based sliding-window rate limiter enforces a limit of 100 requests per minute per IP address. Requests exceeding the limit receive a `429 Too Many Requests` response.

---

## Future Improvements

| Improvement | Description |
|---|---|
| Authentication | JWT-based login with protected routes |
| Role-based access | Admin, editor, and viewer roles |
| OAuth login | Google / GitHub SSO |
| Multiple LLM providers | Switch between Groq, OpenAI, Anthropic via config |
| Unit and integration tests | pytest with async test client and factory fixtures |
| OpenTelemetry tracing | Distributed tracing across FastAPI and Celery |
| Prometheus + Grafana | Metrics collection and dashboards |
| CI/CD pipeline | GitHub Actions for lint, test, and Docker build |
| Kubernetes deployment | Helm chart for production-grade orchestration |
| Cloud deployment | AWS ECS / GCP Cloud Run deployment guide |
| Unsubscribe link | One-click unsubscribe flow with token validation |
| Article editing | In-dashboard article editor with preview |

---

## Contributing

Contributions, bug reports, and feature requests are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request against `main`

Please keep PRs focused and include a clear description of what changed and why.

---

## License

This project is licensed under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```