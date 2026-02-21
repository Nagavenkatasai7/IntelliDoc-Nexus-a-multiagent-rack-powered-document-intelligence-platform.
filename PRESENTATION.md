# IntelliDoc Nexus: Multi-Agent RAG-Powered Document Intelligence Platform

## Presentation Script (30 Minutes)

---

> **HOW TO USE THIS SCRIPT:**
> - Each section has a **[TIME]** marker showing how long to spend on it
> - **Bold text** = key phrases to emphasize when speaking
> - `Code blocks` = things to show on screen or type during live demo
> - *Italics* = stage directions (what to click, show, or do)
> - Bullet points under "TALKING POINTS" = what to say naturally in your own words
> - The text under "SAY:" is the exact script you can follow word-for-word

---

## SLIDE 1: Title & Introduction [2 minutes]

### SAY:

"Good morning/afternoon everyone. My name is [YOUR NAME], and today I'm going to walk you through **IntelliDoc Nexus** - a production-grade, multi-agent **Retrieval-Augmented Generation** platform that I designed and built from the ground up.

This is not a tutorial project. This is not a to-do app. This is a **full-stack AI system** that takes real documents - PDFs, Word files, text files - processes them through a sophisticated machine learning pipeline, stores them in a vector database, and then uses **five specialized AI agents** working together to answer questions about those documents with **source citations** and **real-time streaming responses**.

I built this to demonstrate that I can take a complex, ambiguous problem - 'make documents intelligent' - and turn it into a **working, deployed, production-ready system** with proper architecture, testing, error handling, and DevOps.

Let me show you exactly how I did it."

---

## SLIDE 2: The Problem I Solved [3 minutes]

### SAY:

"Before I get into the technical details, let me explain the **real-world problem** this solves, because understanding the problem is half the engineering.

Organizations today are drowning in documents. Research papers, legal contracts, technical manuals, policy documents. The knowledge is there, but **finding specific information** across hundreds of pages is painful. You end up with three problems:

**Problem 1: Information Retrieval.** Traditional keyword search fails when you're looking for concepts, not exact words. If I search for 'cost optimization' but my document says 'reducing expenses,' keyword search won't find it.

**Problem 2: Context Synthesis.** Even if you find the right paragraphs, you still have to read through them, understand them, and synthesize an answer. That takes time, and humans miss things.

**Problem 3: Trustworthiness.** If I use ChatGPT to answer a question about my documents, it might hallucinate - it might give me a confident answer that's completely made up. There's no way to verify where the information came from.

**IntelliDoc Nexus solves all three.** It uses **semantic search** to find relevant content by meaning, not just keywords. It uses **multiple AI agents** to synthesize, cite, and verify the answer. And it provides **source citations** so you can trace every claim back to the exact document and page number.

This is the same architecture that companies like **Notion, Glean, and Perplexity AI** use in production."

---

## SLIDE 3: Architecture Overview [5 minutes]

### SAY:

"Let me walk you through the **system architecture**. I want you to see that this isn't just code thrown together - it's a **deliberately designed system** with clear separation of concerns.

*Show architecture diagram*

At the highest level, IntelliDoc Nexus has **four containerized services** orchestrated with **Docker Compose**:

1. **React Frontend** on port 3000 - A modern single-page application built with TypeScript, React 18, TailwindCSS, and Zustand for state management.

2. **FastAPI Backend** on port 8000 - An async Python API server with 18 REST endpoints, handling everything from document upload to real-time chat streaming.

3. **PostgreSQL 16** - Our primary data store for documents, chunks, chat sessions, and user data. With proper migrations managed by Alembic.

4. **Redis 7** - Used as a message broker for Celery background tasks and for caching.

Now let me zoom into the backend, because that's where the interesting engineering is.

**The backend is organized into four layers:**

- **API Layer** - FastAPI routes with dependency injection, request validation via Pydantic v2, and proper HTTP status codes.
- **Service Layer** - Business logic: document processing, chunking, embedding, vector storage, BM25 search, and the RAG pipeline.
- **Agent Layer** - Five specialized AI agents: Retrieval, Synthesis, Citation, Reflection, and an Orchestrator that coordinates them all.
- **Data Layer** - SQLAlchemy 2.0 async ORM with cross-database type compatibility I built from scratch.

**Key architectural decisions I made:**

- **Async everywhere.** The entire backend is async using `asyncio`, `asyncpg`, and async SQLAlchemy. This means the server can handle hundreds of concurrent requests without blocking.
- **Lazy loading for heavy dependencies.** Libraries like `sentence-transformers`, `anthropic`, and `pinecone` are only imported when first needed. This cuts startup time from 30 seconds to under 3 seconds.
- **Namespace-based multi-tenancy.** Each user's vectors are stored in a separate Pinecone namespace. This means user data is isolated at the infrastructure level, not just the application level.
- **Hybrid search with Reciprocal Rank Fusion.** I combine dense vector search (semantic) with sparse BM25 search (keyword) using RRF scoring. This gives better retrieval than either method alone. This is the same technique used in production by **Microsoft Bing** and **Elasticsearch 8**."

---

## SLIDE 4: The Tech Stack [3 minutes]

### SAY:

"Let me break down the **complete tech stack** and why I chose each technology. These weren't random choices - each one was selected for a specific reason.

**Frontend:**
- **React 18 with TypeScript** - Type safety, component architecture, and the largest ecosystem.
- **TailwindCSS** - Utility-first CSS for rapid, consistent UI development. No custom CSS classes to maintain.
- **Zustand** for global state - Lightweight alternative to Redux. Zero boilerplate, 1KB bundle. I chose it over Redux because for this application's state complexity, Redux would be over-engineering.
- **TanStack React Query** for server state - Automatic caching, background refetching, optimistic updates. This is the industry standard for managing server state in React.
- **Vite** as the build tool - 10x faster HMR than webpack. Sub-second hot reload during development.

**Backend:**
- **FastAPI** - The fastest Python web framework. Built-in OpenAPI docs, async support, dependency injection, and Pydantic validation. I chose it over Django REST Framework because async performance was critical for streaming chat.
- **SQLAlchemy 2.0 (Async)** - The most mature Python ORM, now with first-class async support. I use it with asyncpg for PostgreSQL.
- **Anthropic Claude API** - Claude Sonnet for synthesis (high quality), Claude Haiku for lightweight agent tasks (low cost). I designed the system so the model can be swapped without changing business logic.
- **Pinecone** (Serverless) - Managed vector database. I chose it over self-hosted alternatives like ChromaDB or Qdrant because in production you want managed infrastructure. Pinecone handles scaling, replication, and availability.
- **Sentence-Transformers** - I use the `all-MiniLM-L6-v2` model for generating 384-dimensional embeddings locally. It's fast, accurate, and doesn't require API calls.
- **Pydantic v2** - Data validation and serialization. The v2 rewrite in Rust makes it 5-17x faster than v1.

**Infrastructure:**
- **Docker Compose** - Four services, health checks, volume mounts, environment management.
- **Alembic** - Database migrations. Version-controlled schema changes.
- **Prometheus** - Metrics collection for observability.
- **Structlog** - Structured logging with JSON output for production log aggregation.

**Testing:**
- **Pytest** with async support - 103 tests covering unit, integration, and load testing.
- **Locust** for load testing - Simulates concurrent users hitting all endpoints."

---

## SLIDE 5: Deep Dive - The RAG Pipeline [5 minutes]

### SAY:

"Now let me go deep on the **most technically interesting part** of this project: the RAG pipeline. RAG stands for **Retrieval-Augmented Generation**, and it's the core innovation that makes this system actually useful.

**Why RAG matters:** Large language models like Claude are incredibly powerful, but they have two fundamental limitations. First, they can hallucinate - generate confident answers that are factually wrong. Second, they have a knowledge cutoff - they don't know about your private documents. RAG solves both problems by **retrieving relevant context** from your actual documents and passing it to the LLM along with the question.

**Here's how my RAG pipeline works, step by step:**

### Stage 1: Document Ingestion

When a user uploads a document, it goes through a **seven-step pipeline:**

1. **File validation** - Type checking, size limits (100MB max), extension mapping.
2. **Duplicate detection** - SHA-256 content hashing. If you upload the same file twice, the system recognizes it instantly.
3. **Text extraction** - I use `pdfplumber` for PDFs (with table extraction), `python-docx` for Word files, and UTF-8 decoding for text files. I had to build a **text sanitization layer** to handle null bytes and control characters that PDFs produce - PostgreSQL rejects these, so I strip them during extraction.
4. **Semantic chunking** - This is where it gets interesting. I don't just split on every 1000 tokens. I detect **heading patterns and section boundaries** using regex, then split at **sentence boundaries** with configurable overlap. This preserves semantic coherence within each chunk. Each chunk knows its page number and section title.
5. **Embedding generation** - Each chunk is embedded into a 384-dimensional vector using SentenceTransformers. I batch this in groups of 32 to prevent memory issues on large documents.
6. **Vector upsert** - Embeddings are stored in Pinecone with metadata (document ID, chunk index, page number, content preview).
7. **BM25 indexing** - Simultaneously, chunks are tokenized and added to an in-memory BM25 index for keyword search.

### Stage 2: Hybrid Retrieval

When a user asks a question, I run **two search strategies in parallel:**

- **Dense search** via Pinecone - Converts the question to a vector and finds the most semantically similar chunks. This catches conceptual matches: 'cost reduction' matches 'reducing expenses.'
- **Sparse search** via BM25 - Traditional keyword matching with TF-IDF scoring. This catches exact term matches that vector search might miss.

I then combine these results using **Reciprocal Rank Fusion** with `k=60`. The formula is:

```
RRF_score(item) = sum(1 / (k + rank_in_list)) for each list containing the item
```

Items appearing in both dense AND sparse results get a higher combined score. This consistently outperforms either method alone - research papers show **5-15% improvement in retrieval accuracy** with hybrid search.

### Stage 3: Context Enrichment

After retrieval, I **enrich the context** by fetching full chunk content from PostgreSQL. Pinecone metadata is limited in size, but the database has the complete text. This means Claude gets full paragraphs, not truncated previews.

### Stage 4: Generation with Citations

The enriched context is formatted with source markers (`[Source 1]`, `[Source 2]`) and passed to Claude with a system prompt that instructs it to always cite sources. The response streams back in real-time via **Server-Sent Events**.

This is the same RAG architecture that powers products like **Notion AI, GitHub Copilot's codebase search, and Perplexity AI**."

---

## SLIDE 6: Deep Dive - Multi-Agent System [4 minutes]

### SAY:

"On top of the standard RAG pipeline, I built a **multi-agent system** with five specialized agents. This demonstrates understanding of agentic AI architecture - one of the hottest areas in AI engineering right now.

**Why multiple agents?** A single LLM call can answer questions, but the quality improves dramatically when you decompose the task into specialized steps with **quality control loops.**

**Here are my five agents:**

1. **Retrieval Agent** - Analyzes the question and decides the optimal retrieval strategy. Should it do a broad search or a focused one? Should it increase the top-k parameter for complex questions? It uses Claude Haiku for speed.

2. **Synthesis Agent** - Takes the retrieved context and generates a comprehensive answer. This uses Claude Sonnet - the most capable model - because synthesis quality is the most important factor in user satisfaction.

3. **Citation Agent** - Reviews the synthesis output and verifies that every claim is backed by a source. It adds, corrects, or removes citation markers. This is the **trust layer** - it ensures the response is grounded in actual documents.

4. **Reflection Agent** - Evaluates the complete response for quality. Does it actually answer the question? Is it clear and well-structured? Are the citations accurate? If the quality score is below a threshold, it **sends the response back for revision**. This creates a self-improving loop.

5. **Orchestrator Agent** - Coordinates the entire pipeline: Retrieval -> Synthesis -> Citation -> Reflection -> (optional revision loop). It manages state between agents and tracks the agent trace for debugging.

**The key insight** is that each agent has a single responsibility. The synthesis agent doesn't worry about citations - that's the citation agent's job. The citation agent doesn't worry about quality - that's the reflection agent's job. This **separation of concerns** makes each agent simpler, more reliable, and easier to debug.

**I implemented this using a state machine pattern** - each agent reads from and writes to a shared state dictionary. The orchestrator controls transitions between states. This is architecturally similar to **LangGraph** but I built it from scratch to avoid the dependency and to demonstrate that I understand the underlying pattern, not just the library API."

---

## SLIDE 7: Live Demo [5 minutes]

### SAY:

"Now let me show you the system running live. Everything is running in Docker on my local machine."

*Open browser to http://localhost:3000*

### Demo Script:

**Step 1: Show the UI**
"Here's the application. On the left, you have the sidebar with document upload, document list, and chat history. In the center is the chat interface. At the top, you can switch between Chat and Search modes. There's dark mode support as well."

*Toggle dark mode to show it works*

**Step 2: Upload a document**
"Let me upload a document. I'll drag and drop this PDF."

*Upload a document. Point out the upload status: Uploading -> Processing -> Complete*

"Notice the status indicators - Uploading, then Processing (that's the embedding step), then the green checkmark. Under the hood, the system just extracted text, chunked it into semantic sections, generated embeddings for each chunk, stored them in Pinecone, and indexed them for keyword search. All in a few seconds."

**Step 3: Ask a question**
"Now let me ask a question. Watch the response stream in real-time."

*Type a question and submit*

"See how the response is streaming token by token? That's Server-Sent Events from the backend. And look at the bottom - source citations. Each `[Source N]` links back to a specific document, page, and section. You can expand the citations panel to see the actual text that was referenced."

**Step 4: Multi-document query**
"Now let me select multiple documents and ask a cross-document question."

*Select 2-3 documents in the sidebar, then ask a comparison question*

"Notice how the response synthesizes information from **multiple documents** and cites each one separately. This is the hybrid search and context enrichment working together."

**Step 5: Semantic Search**
"Let me switch to Search mode. This is a direct semantic search - no LLM involved, just vector similarity."

*Switch to Search tab, type a query*

"Each result shows the document name, relevance score, page number, and a preview. This is useful when you want to find specific passages without generating a full answer."

**Step 6: Show the API docs**

*Open http://localhost:8000/docs in a new tab*

"The backend automatically generates interactive API documentation via OpenAPI/Swagger. Every endpoint is documented with request schemas, response models, and you can test them directly from this page. There are 18 endpoints covering auth, documents, chat, sessions, search, health, and metrics."

**Step 7: Show the Docker setup**

*Show terminal with `docker compose ps`*

"Four containers running: the React frontend, FastAPI backend, PostgreSQL, and Redis. All with health checks, volume mounts for development, and proper networking."

---

## SLIDE 8: Engineering Challenges I Solved [5 minutes]

### SAY:

"Building this system wasn't straightforward. I ran into **real engineering problems** that required creative solutions. Let me walk you through the most significant ones, because I think **problem-solving ability** is what separates a junior developer from someone who can actually build production systems.

### Challenge 1: Null Bytes in PDF Extraction

**The problem:** When users uploaded certain academic PDFs, the upload would crash with a 500 error. The logs showed `CharacterNotInRepertoireError: invalid byte sequence for encoding UTF8: 0x00`. Basically, the PDF text extractor was producing content with null bytes from math symbols and special characters, and PostgreSQL cannot store null bytes in TEXT columns.

**My solution:** I built a **text sanitization layer** in the document processor that strips null bytes and problematic control characters while preserving legitimate Unicode. This runs on all extracted text before database storage. The key insight was that this isn't a rare edge case - it affects any PDF with mathematical notation, which is most academic papers.

### Challenge 2: Streaming Response Database Consistency

**The problem:** In the streaming chat endpoint, FastAPI returns a `StreamingResponse` generator immediately. But the dependency injection system runs its cleanup (database commit) when the endpoint *returns*, not when the generator *finishes*. This meant the assistant's message was being committed before it existed.

**My solution:** I pre-commit the session and user message before returning the streaming response, then use a **fresh database session inside the generator** to save the completed assistant message. This ensures database consistency without blocking the stream.

### Challenge 3: Ephemeral BM25 Index

**The problem:** The BM25 keyword search index is in-memory. Every time the Docker container restarted, the index was empty. This meant hybrid search degraded to only vector search, reducing retrieval quality.

**My solution:** I added a **startup hook** that rebuilds the BM25 index from all existing document chunks in PostgreSQL. On container start, it loads all completed documents, tokenizes their chunks, and builds the BM25 index. This takes less than a second for thousands of chunks.

### Challenge 4: Cross-Database Type Compatibility

**The problem:** My SQLAlchemy models used PostgreSQL-specific types (UUID, JSONB, ARRAY) for production, but my test suite needed to run on SQLite for speed. SQLite doesn't support any of these types.

**My solution:** I built **custom TypeDecorator classes** - `GUID`, `JSONType`, and `ArrayType` - that automatically detect the database dialect and use the appropriate native type. On PostgreSQL, `GUID` uses the native `UUID` type. On SQLite, it uses `CHAR(36)`. This let me run 103 tests in 7 seconds on SQLite while keeping full PostgreSQL compatibility in production.

### Challenge 5: Frontend Streaming Error Recovery

**The problem:** The original streaming implementation used a fire-and-forget `fetch().then()` pattern. If the stream failed (network error, timeout, server crash), the error was silently swallowed and the UI got permanently stuck in a loading state with no way to recover.

**My solution:** I rewrote the streaming function as a proper `async/await` with an `AbortController` timeout, HTTP status checking, error propagation, and a fallback to non-streaming mode. If streaming fails mid-response, the partial content is preserved with an '[interrupted]' marker instead of being lost."

---

## SLIDE 9: Testing & Quality [2 minutes]

### SAY:

"Production-ready code needs production-ready testing. Let me show you what I built.

**103 automated tests** across multiple layers:

- **Unit tests** for the RAG pipeline: Reciprocal Rank Fusion scoring, context building, message construction, source extraction. I test edge cases like empty results, single-source results, and score normalization.

- **Unit tests** for the multi-agent system: State management, retrieval strategy selection, rank fusion scoring, and edge cases for each agent.

- **Unit tests** for the ingestion pipeline: File extension mapping, content hashing, filename extraction, chunk boundary detection.

- **Integration tests**: Session CRUD operations, health endpoint, metrics endpoint, end-to-end chat flow.

- **Load tests** with Locust: I built user behavior profiles that simulate realistic usage patterns - uploading documents, asking questions, searching - to measure throughput and latency under load.

I also set up **Alembic migrations** for version-controlled database schema changes, which is essential for any production deployment.

All tests run in **7.7 seconds** on a SQLite backend, which makes them fast enough to run on every commit in a CI/CD pipeline."

---

## SLIDE 10: Project Metrics & What I Built [2 minutes]

### SAY:

"Let me give you the numbers on what this project contains:

- **99 source files** across backend, frontend, tests, and infrastructure
- **6,700+ lines of code** - all hand-written, architecturally intentional
- **49 Python modules** in the backend
- **20 TypeScript/React components** in the frontend
- **18 REST API endpoints** covering auth, documents, chat, sessions, search, health, and metrics
- **5 AI agents** with a state machine orchestrator
- **103 automated tests** with unit, integration, and load testing
- **4 Docker services** with health checks and persistent volumes
- **Hybrid search** combining dense (vector) and sparse (BM25) retrieval
- **Real-time streaming** via Server-Sent Events
- **Cross-database compatibility** layer for PostgreSQL and SQLite
- **Dark mode** UI with responsive design

This is not a weekend project. This is a **production-grade system** built with the same patterns and practices used at companies like OpenAI, Anthropic, and Google."

---

## SLIDE 11: Key Concepts I Mastered [3 minutes]

### SAY:

"Let me summarize the **key technical concepts** I demonstrated in this project. Each of these is a skill that's in high demand right now:

**1. Retrieval-Augmented Generation (RAG)**
- Document ingestion pipelines with multi-format extraction
- Semantic chunking with heading detection and sentence-boundary overlap
- Embedding generation with SentenceTransformers
- Vector storage and similarity search with Pinecone
- Context enrichment and citation generation

**2. Agentic AI Architecture**
- Multi-agent systems with specialized roles
- State machine orchestration patterns
- Self-improving loops with reflection and revision
- Separation of concerns in AI pipeline design

**3. Full-Stack Engineering**
- Async Python with FastAPI, SQLAlchemy 2.0, asyncpg
- React 18 with TypeScript, Zustand, TanStack Query
- Real-time streaming with Server-Sent Events
- RESTful API design with proper status codes and validation

**4. Data Engineering**
- Hybrid search combining dense and sparse retrieval
- Reciprocal Rank Fusion for result merging
- Vector database management with Pinecone
- PostgreSQL with async ORM and cross-database compatibility

**5. DevOps & Production Readiness**
- Docker Compose multi-service orchestration
- Database migrations with Alembic
- Prometheus metrics and structured logging
- Health checks, rate limiting, security headers
- Comprehensive automated testing

**6. Problem Solving**
- Debugging production issues: null bytes, streaming consistency, memory management
- Designing for resilience: timeout handling, error recovery, graceful degradation
- Performance optimization: lazy loading, batch processing, caching"

---

## SLIDE 12: What Makes This Different [2 minutes]

### SAY:

"I want to address why this project stands out compared to other portfolio projects you might see.

**First, it's production-grade, not proof-of-concept.** It has error handling, input validation, rate limiting, security headers, structured logging, metrics, health checks, and automated tests. Most portfolio RAG projects skip all of this.

**Second, it's a complete system.** Frontend, backend, database, vector store, search index, AI pipeline, agents, testing, Docker - it's the full picture. I didn't just build an API and call it done.

**Third, I solved real engineering problems.** The null byte issue, the streaming database consistency, the BM25 index persistence, the cross-database compatibility - these are the kinds of problems you encounter in production, and I solved each one with a proper engineering approach, not a hack.

**Fourth, I understand the theory behind the code.** I can explain why Reciprocal Rank Fusion works, why hybrid search outperforms single-strategy retrieval, why multi-agent systems produce better results than single-prompt approaches, and why specific architectural decisions were made.

**This project demonstrates that I can take an ambiguous, complex problem and deliver a working, well-architected, production-ready solution.**"

---

## SLIDE 13: Future Improvements [1 minute]

### SAY:

"No system is ever truly finished. Here's what I'd add next:

- **Kubernetes deployment** with horizontal pod autoscaling for the backend
- **OAuth 2.0 / SSO authentication** to replace the development placeholder
- **WebSocket support** for bi-directional real-time communication
- **Multi-modal RAG** - processing images and charts within documents
- **Fine-tuned embedding model** trained on domain-specific data
- **CI/CD pipeline** with GitHub Actions for automated testing and deployment
- **Cost optimization** through response caching and adaptive model selection

Each of these is a weekend to a week of work, and I have a clear implementation plan for each one."

---

## SLIDE 14: Closing & Q&A [1 minute]

### SAY:

"To summarize: **IntelliDoc Nexus** is a full-stack, multi-agent RAG platform that demonstrates my ability to:

- **Design** complex system architectures
- **Implement** production-grade code across the full stack
- **Integrate** cutting-edge AI technologies (LLMs, vector search, multi-agent systems)
- **Debug** real-world engineering problems
- **Test** thoroughly and think about edge cases
- **Deploy** with proper DevOps practices

I'm excited about building AI-powered products, and I believe this project shows that I have the skills to contribute meaningfully from day one.

Thank you. I'm happy to answer any questions - and I can dive into any part of the codebase live right now if you'd like to see more."

---

## APPENDIX: Quick Reference for Q&A

### Likely Questions & Strong Answers:

**Q: Why did you choose Claude over GPT-4?**
A: "Claude has excellent instruction following for citation tasks, a generous context window, and the streaming API is very clean. That said, I designed the system with a clean abstraction layer - swapping to GPT-4 would require changing one service file, not the entire codebase."

**Q: How would you scale this for production?**
A: "The backend is already async, so it handles concurrency well. For scale: Kubernetes for horizontal scaling, a managed PostgreSQL like RDS or Supabase, Pinecone already scales automatically, and I'd add Redis caching for repeated queries. The BM25 index would move to Elasticsearch for persistence and distribution."

**Q: What was the hardest bug you fixed?**
A: "The streaming database consistency issue. The FastAPI dependency injection commits when the endpoint returns, but with streaming, the generator outlives the endpoint. I had to pre-commit the session and create a fresh database session inside the generator. It required understanding how Python async generators interact with FastAPI's middleware lifecycle."

**Q: How do you handle documents uploaded before vector search was configured?**
A: "Good question - this actually happened during development. Documents uploaded without Pinecone only have BM25 index entries. I built the system to gracefully handle partial indexing, and there's a re-indexing path through the ingestion service. The hybrid search still works with just BM25 results, just with lower quality."

**Q: Why not use LangChain?**
A: "LangChain is great for prototyping, but I wanted to demonstrate understanding of the underlying patterns, not framework proficiency. Building the RAG pipeline and multi-agent system from scratch gave me full control over the behavior and made debugging much easier. In a production setting, I'd evaluate LangChain/LlamaIndex based on the team's needs."

**Q: What's the latency like?**
A: "Non-streaming RAG responses are 3-5 seconds. Streaming starts producing tokens in under 2 seconds. The bottleneck is the Claude API call, not my infrastructure. Document upload with embedding takes 1-2 seconds for small files, 15-20 seconds for large PDFs."

**Q: How does the hybrid search actually improve results?**
A: "Vector search catches semantic similarity - 'cost reduction' matches 'reducing expenses.' BM25 catches exact keyword matches that vector search might rank lower. Reciprocal Rank Fusion combines both ranking signals. Research consistently shows 5-15% retrieval accuracy improvement with hybrid over single-strategy search."

---

## DEMO CHECKLIST

Before the presentation, verify:

- [ ] Docker containers are all running: `docker compose ps`
- [ ] Backend health check passes: `curl http://localhost:8000/api/v1/health`
- [ ] Frontend loads at: `http://localhost:3000`
- [ ] At least 2-3 documents are uploaded and processed
- [ ] Test a chat query to warm up the embedding model
- [ ] Test search to verify Pinecone connection
- [ ] Have a sample PDF ready to upload during demo
- [ ] Swagger docs load at: `http://localhost:8000/docs`
- [ ] Browser is in a clean state (no previous errors in console)

---

*Total presentation time: ~30 minutes including live demo*
*Recommended: Practice the demo section 2-3 times before the actual presentation*
