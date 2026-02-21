#!/usr/bin/env python3
"""Generate a professional PDF presentation from the IntelliDoc Nexus project."""

from fpdf import FPDF
import re

# ──────────────────────────────────────────────────────────────
# Colour palette
# ──────────────────────────────────────────────────────────────
NAVY      = (15, 23, 42)
WHITE     = (255, 255, 255)
BLUE      = (59, 130, 246)
LIGHT_BG  = (248, 250, 252)
GRAY      = (100, 116, 139)
DARK_GRAY = (51, 65, 85)
GREEN     = (34, 197, 94)
ACCENT    = (99, 102, 241)  # indigo

class PresentationPDF(FPDF):
    current_slide = 0
    total_slides  = 0
    slide_title   = ""

    def header(self):
        if self.current_slide == 0:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 6, "IntelliDoc Nexus  |  Presentation Script", align="L")
        self.ln(2)
        # accent line
        self.set_draw_color(*BLUE)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(4)

    def footer(self):
        if self.current_slide == 0:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    # ── helpers ──────────────────────────────────────────────
    def section_title(self, text, time_hint=""):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*NAVY)
        self.cell(0, 12, text, new_x="LMARGIN", new_y="NEXT")
        if time_hint:
            self.set_font("Helvetica", "I", 10)
            self.set_text_color(*BLUE)
            self.cell(0, 6, time_hint, new_x="LMARGIN", new_y="NEXT")
        # underline
        self.set_draw_color(*BLUE)
        self.set_line_width(0.6)
        y = self.get_y() + 1
        self.line(10, y, 80, y)
        self.ln(6)

    def sub_heading(self, text):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*ACCENT)
        self.ln(3)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*DARK_GRAY)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def speaker_note(self, text):
        """Yellow-highlighted speaker note block."""
        self.set_fill_color(254, 249, 195)  # light yellow
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(120, 80, 0)
        x = self.get_x()
        w = self.w - 20
        self.set_x(10)
        self.multi_cell(w, 5.2, text, fill=True)
        self.ln(2)

    def bullet(self, text, indent=0, bold_prefix=""):
        x_start = 14 + indent
        self.set_x(x_start)
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*DARK_GRAY)
        # bullet char (use dash since core fonts don't support unicode bullet)
        self.cell(5, 5.5, "-")
        if bold_prefix:
            self.set_font("Helvetica", "B", 10.5)
            self.cell(self.get_string_width(bold_prefix) + 1, 5.5, bold_prefix)
            self.set_font("Helvetica", "", 10.5)
            self.multi_cell(0, 5.5, text)
        else:
            self.multi_cell(0, 5.5, text)
        self.ln(0.5)

    def tech_badge(self, items):
        """Row of coloured tech badges."""
        self.ln(1)
        x = 12
        for item in items:
            w = self.get_string_width(item) + 8
            if x + w > self.w - 10:
                self.ln(8)
                x = 12
            self.set_xy(x, self.get_y())
            self.set_fill_color(*BLUE)
            self.set_text_color(*WHITE)
            self.set_font("Helvetica", "B", 8.5)
            self.cell(w, 7, item, fill=True, align="C")
            x += w + 3
        self.ln(10)

    def stat_box(self, label, value):
        w = 42
        h = 22
        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(*LIGHT_BG)
        self.rect(x, y, w, h, "F")
        self.set_draw_color(*BLUE)
        self.set_line_width(0.4)
        self.line(x, y, x, y + h)  # left accent
        self.set_xy(x + 3, y + 2)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*BLUE)
        self.cell(w - 6, 8, str(value))
        self.set_xy(x + 3, y + 11)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(w - 6, 6, label)
        self.set_xy(x + w + 4, y)

    def page_break_if_needed(self, space=40):
        if self.get_y() > self.h - space:
            self.add_page()


# ══════════════════════════════════════════════════════════════
# BUILD THE PDF
# ══════════════════════════════════════════════════════════════

pdf = PresentationPDF("P", "mm", "A4")
pdf.set_auto_page_break(auto=True, margin=20)
pdf.set_margins(10, 10, 10)

# ── COVER PAGE ───────────────────────────────────────────────
pdf.add_page()
pdf.current_slide = 0

# Navy background block
pdf.set_fill_color(*NAVY)
pdf.rect(0, 0, 210, 160, "F")

# Title
pdf.set_y(45)
pdf.set_font("Helvetica", "B", 32)
pdf.set_text_color(*WHITE)
pdf.cell(0, 14, "IntelliDoc Nexus", align="C", new_x="LMARGIN", new_y="NEXT")

pdf.set_font("Helvetica", "", 14)
pdf.set_text_color(148, 163, 184)
pdf.cell(0, 8, "Multi-Agent RAG-Powered Document Intelligence Platform", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(6)

# Accent line
pdf.set_draw_color(*BLUE)
pdf.set_line_width(1)
pdf.line(60, pdf.get_y(), 150, pdf.get_y())
pdf.ln(10)

pdf.set_font("Helvetica", "", 12)
pdf.set_text_color(*WHITE)
pdf.cell(0, 7, "Technical Presentation & Live Demo", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 7, "30-Minute Walkthrough", align="C", new_x="LMARGIN", new_y="NEXT")

# Below navy block
pdf.set_y(170)
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(*DARK_GRAY)
pdf.cell(0, 7, "Presented by: [YOUR NAME]", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 7, "[YOUR TITLE / ROLE]", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 7, "[DATE]", align="C", new_x="LMARGIN", new_y="NEXT")

pdf.ln(12)
pdf.set_font("Helvetica", "I", 9)
pdf.set_text_color(*GRAY)
pdf.cell(0, 6, "Built with: Python  |  React  |  FastAPI  |  PostgreSQL  |  Pinecone  |  Claude API  |  Docker", align="C")

# ── SLIDE 1 : AGENDA ────────────────────────────────────────
pdf.add_page()
pdf.current_slide = 1
pdf.section_title("Agenda", "30-Minute Presentation")

agenda = [
    ("1.", "Introduction & Project Overview", "2 min"),
    ("2.", "The Problem I Solved", "3 min"),
    ("3.", "System Architecture", "5 min"),
    ("4.", "Tech Stack Deep Dive", "3 min"),
    ("5.", "RAG Pipeline Explained", "5 min"),
    ("6.", "Multi-Agent System", "4 min"),
    ("7.", "Live Demo", "5 min"),
    ("8.", "Engineering Challenges", "5 min"),
    ("9.", "Testing & Quality Assurance", "2 min"),
    ("10.", "Project Metrics & Achievements", "2 min"),
    ("11.", "Key Concepts Mastered", "3 min"),
    ("12.", "What Makes This Different", "2 min"),
    ("13.", "Future Roadmap & Q&A", "2 min"),
]

for num, title, time in agenda:
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*NAVY)
    pdf.cell(8, 7, num)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*DARK_GRAY)
    pdf.cell(120, 7, title)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 7, time, new_x="LMARGIN", new_y="NEXT")

# ── SLIDE 2 : INTRODUCTION ──────────────────────────────────
pdf.add_page()
pdf.current_slide = 2
pdf.section_title("Introduction & Project Overview", "[2 minutes]")

pdf.speaker_note(
    "SAY: \"Good morning/afternoon everyone. My name is [YOUR NAME], and today I'm going to walk you "
    "through IntelliDoc Nexus - a production-grade, multi-agent Retrieval-Augmented Generation platform "
    "that I designed and built from the ground up.\""
)

pdf.body(
    "IntelliDoc Nexus is a full-stack AI system that takes real documents - PDFs, Word files, "
    "text files - processes them through a sophisticated machine learning pipeline, stores them "
    "in a vector database, and uses five specialized AI agents working together to answer "
    "questions about those documents with source citations and real-time streaming responses."
)

pdf.speaker_note(
    "SAY: \"This is not a tutorial project. This is not a to-do app. This is a full-stack AI system "
    "that demonstrates I can take a complex, ambiguous problem and turn it into a working, deployed, "
    "production-ready system with proper architecture, testing, error handling, and DevOps.\""
)

pdf.sub_heading("At a Glance")
pdf.ln(2)
# Stats row
y_stats = pdf.get_y()
pdf.stat_box("Source Files", "99")
pdf.stat_box("Lines of Code", "6,700+")
pdf.stat_box("Automated Tests", "103")
pdf.stat_box("Docker Services", "4")
pdf.set_y(y_stats + 28)

# ── SLIDE 3 : THE PROBLEM ───────────────────────────────────
pdf.add_page()
pdf.current_slide = 3
pdf.section_title("The Problem I Solved", "[3 minutes]")

pdf.speaker_note(
    "SAY: \"Before I get into the technical details, let me explain the real-world problem this solves, "
    "because understanding the problem is half the engineering.\""
)

pdf.body(
    "Organizations today are drowning in documents. Research papers, legal contracts, technical "
    "manuals, policy documents. The knowledge is there, but finding specific information across "
    "hundreds of pages is painful."
)

pdf.sub_heading("Three Core Problems")

problems = [
    ("Problem 1: Information Retrieval. ",
     "Traditional keyword search fails when you're looking for concepts, not exact words. "
     "If I search for 'cost optimization' but my document says 'reducing expenses,' keyword search won't find it."),
    ("Problem 2: Context Synthesis. ",
     "Even if you find the right paragraphs, you still have to read through them, understand them, "
     "and synthesize an answer. That takes time, and humans miss things."),
    ("Problem 3: Trustworthiness. ",
     "If I use ChatGPT to answer a question about my documents, it might hallucinate - give a confident "
     "answer that's completely made up. There's no way to verify where the information came from."),
]
for bold, text in problems:
    pdf.bullet(text, bold_prefix=bold)

pdf.ln(3)
pdf.speaker_note(
    "SAY: \"IntelliDoc Nexus solves all three. It uses semantic search to find relevant content by meaning. "
    "It uses multiple AI agents to synthesize, cite, and verify the answer. And it provides source citations "
    "so you can trace every claim back to the exact document and page number. This is the same architecture "
    "that companies like Notion, Glean, and Perplexity AI use in production.\""
)

# ── SLIDE 4 : ARCHITECTURE ──────────────────────────────────
pdf.add_page()
pdf.current_slide = 4
pdf.section_title("System Architecture", "[5 minutes]")

pdf.speaker_note(
    "SAY: \"Let me walk you through the system architecture. I want you to see that this isn't code thrown "
    "together - it's a deliberately designed system with clear separation of concerns.\""
)

pdf.sub_heading("Four Containerized Services")
services = [
    ("React Frontend (Port 3000) - ",
     "Modern SPA with TypeScript, React 18, TailwindCSS, Zustand for state management."),
    ("FastAPI Backend (Port 8000) - ",
     "Async Python API server with 18 REST endpoints, real-time SSE streaming."),
    ("PostgreSQL 16 - ",
     "Primary data store for documents, chunks, sessions, users. Migrations via Alembic."),
    ("Redis 7 - ",
     "Message broker for Celery background tasks and caching layer."),
]
for bold, text in services:
    pdf.bullet(text, bold_prefix=bold)

pdf.sub_heading("Backend Architecture Layers")
layers = [
    ("API Layer - ", "FastAPI routes, dependency injection, Pydantic v2 validation, proper HTTP status codes."),
    ("Service Layer - ", "Document processing, chunking, embedding, vector storage, BM25 search, RAG pipeline."),
    ("Agent Layer - ", "Five specialized AI agents: Retrieval, Synthesis, Citation, Reflection, Orchestrator."),
    ("Data Layer - ", "SQLAlchemy 2.0 async ORM with custom cross-database type compatibility."),
]
for bold, text in layers:
    pdf.bullet(text, bold_prefix=bold)

pdf.page_break_if_needed(70)
pdf.sub_heading("Key Architectural Decisions")

decisions = [
    ("Async everywhere. ",
     "The entire backend uses asyncio, asyncpg, and async SQLAlchemy. Handles hundreds of concurrent "
     "requests without blocking."),
    ("Lazy loading. ",
     "Heavy libraries (sentence-transformers, anthropic, pinecone) are imported on first use. "
     "Cuts startup time from 30s to under 3s."),
    ("Namespace-based multi-tenancy. ",
     "Each user's vectors are in a separate Pinecone namespace. Data isolation at the infrastructure level."),
    ("Hybrid search with RRF. ",
     "Combines dense vector search with sparse BM25 search using Reciprocal Rank Fusion. "
     "Same technique used by Microsoft Bing and Elasticsearch 8."),
]
for bold, text in decisions:
    pdf.bullet(text, bold_prefix=bold)

# ── SLIDE 5 : TECH STACK ────────────────────────────────────
pdf.add_page()
pdf.current_slide = 5
pdf.section_title("Tech Stack Deep Dive", "[3 minutes]")

pdf.speaker_note(
    "SAY: \"Let me break down the complete tech stack and why I chose each technology. "
    "These weren't random choices - each one was selected for a specific reason.\""
)

pdf.sub_heading("Frontend")
pdf.tech_badge(["React 18", "TypeScript", "TailwindCSS", "Zustand", "TanStack Query", "Vite", "Lucide Icons"])

fe_items = [
    ("React 18 + TypeScript - ", "Type safety, component architecture, largest ecosystem."),
    ("Zustand over Redux - ", "Lightweight (1KB), zero boilerplate. Right tool for this app's state complexity."),
    ("TanStack React Query - ", "Automatic caching, background refetching. Industry standard for server state."),
    ("Vite - ", "10x faster HMR than webpack. Sub-second hot reload."),
]
for bold, text in fe_items:
    pdf.bullet(text, bold_prefix=bold)

pdf.sub_heading("Backend")
pdf.tech_badge(["FastAPI", "SQLAlchemy 2.0", "Claude API", "Pinecone", "SentenceTransformers", "Pydantic v2", "Celery"])

be_items = [
    ("FastAPI - ", "Fastest Python framework. Async, auto-docs, dependency injection. Chosen over Django REST for streaming."),
    ("Claude API - ", "Sonnet for synthesis (quality), Haiku for agents (cost). Model-swappable design."),
    ("Pinecone Serverless - ", "Managed vector DB. Chose over ChromaDB/Qdrant for production-grade scaling."),
    ("SentenceTransformers - ", "all-MiniLM-L6-v2 model. 384-dim embeddings generated locally without API calls."),
    ("Pydantic v2 - ", "Rust-based rewrite. 5-17x faster than v1 for validation/serialization."),
]
for bold, text in be_items:
    pdf.bullet(text, bold_prefix=bold)

pdf.sub_heading("Infrastructure & Testing")
pdf.tech_badge(["Docker Compose", "PostgreSQL 16", "Redis 7", "Alembic", "Prometheus", "Structlog", "Pytest", "Locust"])

# ── SLIDE 6 : RAG PIPELINE ──────────────────────────────────
pdf.add_page()
pdf.current_slide = 6
pdf.section_title("Deep Dive: The RAG Pipeline", "[5 minutes]")

pdf.speaker_note(
    "SAY: \"Now let me go deep on the most technically interesting part of this project: the RAG pipeline. "
    "RAG stands for Retrieval-Augmented Generation, and it's the core innovation that makes this system useful.\""
)

pdf.body(
    "Why RAG matters: LLMs are powerful but have two fundamental limitations - they hallucinate "
    "(generate confident but wrong answers) and have a knowledge cutoff (don't know about your "
    "private documents). RAG solves both by retrieving relevant context from actual documents "
    "and passing it to the LLM along with the question."
)

pdf.sub_heading("Stage 1: Document Ingestion (7-Step Pipeline)")
steps = [
    ("1. File Validation - ", "Type checking, size limits (100MB), extension mapping."),
    ("2. Duplicate Detection - ", "SHA-256 content hashing. Instant duplicate recognition."),
    ("3. Text Extraction - ", "pdfplumber for PDFs (with tables), python-docx for Word, UTF-8 for text. Built a sanitization layer for null bytes."),
    ("4. Semantic Chunking - ", "Heading detection + sentence-boundary splits with configurable overlap. Preserves semantic coherence."),
    ("5. Embedding Generation - ", "384-dim vectors via SentenceTransformers. Batched in groups of 32 for memory efficiency."),
    ("6. Vector Upsert - ", "Embeddings stored in Pinecone with metadata (doc ID, chunk index, page, content)."),
    ("7. BM25 Indexing - ", "Chunks tokenized and added to in-memory BM25 index for keyword search."),
]
for bold, text in steps:
    pdf.bullet(text, bold_prefix=bold)

pdf.page_break_if_needed(80)
pdf.sub_heading("Stage 2: Hybrid Retrieval")
pdf.body(
    "When a user asks a question, two search strategies run in parallel:"
)
pdf.bullet("Dense search via Pinecone - Converts question to vector, finds semantically similar chunks. 'Cost reduction' matches 'reducing expenses.'", bold_prefix="")
pdf.bullet("Sparse search via BM25 - Traditional keyword matching with TF-IDF. Catches exact term matches vector search might miss.", bold_prefix="")

pdf.ln(2)
pdf.body(
    "Results are combined using Reciprocal Rank Fusion (k=60): "
    "RRF_score(item) = sum(1/(k + rank)) for each list containing the item. "
    "Items appearing in BOTH lists get higher scores. Research shows 5-15% retrieval accuracy improvement."
)

pdf.sub_heading("Stage 3: Context Enrichment")
pdf.body(
    "After retrieval, full chunk content is fetched from PostgreSQL (Pinecone metadata is size-limited). "
    "Document names are resolved. Claude gets complete paragraphs, not truncated previews."
)

pdf.sub_heading("Stage 4: Generation with Citations")
pdf.body(
    "Enriched context is formatted with source markers [Source N] and streamed to Claude. "
    "Response streams back via Server-Sent Events in real-time."
)

# ── SLIDE 7 : MULTI-AGENT ───────────────────────────────────
pdf.add_page()
pdf.current_slide = 7
pdf.section_title("Deep Dive: Multi-Agent System", "[4 minutes]")

pdf.speaker_note(
    "SAY: \"On top of the standard RAG pipeline, I built a multi-agent system with five specialized agents. "
    "This demonstrates understanding of agentic AI architecture - one of the hottest areas in AI right now.\""
)

pdf.body(
    "Why multiple agents? A single LLM call can answer questions, but quality improves dramatically "
    "when you decompose the task into specialized steps with quality control loops."
)

pdf.sub_heading("The Five Agents")

agents = [
    ("1. Retrieval Agent - ",
     "Analyzes the question and decides optimal retrieval strategy. Broad or focused? Higher top-k for complex questions? Uses Claude Haiku for speed."),
    ("2. Synthesis Agent - ",
     "Takes retrieved context and generates comprehensive answer. Uses Claude Sonnet (most capable) because synthesis quality drives user satisfaction."),
    ("3. Citation Agent - ",
     "Reviews synthesis output. Verifies every claim is backed by a source. Adds, corrects, or removes citations. This is the trust layer."),
    ("4. Reflection Agent - ",
     "Evaluates complete response for quality. Does it answer the question? Clear? Well-structured? Below threshold? Sends back for revision. Self-improving loop."),
    ("5. Orchestrator Agent - ",
     "Coordinates the pipeline: Retrieval -> Synthesis -> Citation -> Reflection -> (optional revision). Manages state and traces."),
]
for bold, text in agents:
    pdf.bullet(text, bold_prefix=bold)

pdf.ln(3)
pdf.speaker_note(
    "SAY: \"The key insight is separation of concerns. Each agent has a single responsibility. "
    "I implemented this using a state machine pattern - similar to LangGraph but built from scratch "
    "to demonstrate I understand the underlying pattern, not just the library API.\""
)

# ── SLIDE 8 : LIVE DEMO ─────────────────────────────────────
pdf.add_page()
pdf.current_slide = 8
pdf.section_title("Live Demo Script", "[5 minutes]")

pdf.speaker_note(
    "SAY: \"Now let me show you the system running live. Everything is running in Docker on my local machine.\""
)

demo_steps = [
    ("Step 1: Show the UI. ",
     "Open http://localhost:3000. Point out sidebar (upload, documents, history), chat area, search tab, dark mode toggle."),
    ("Step 2: Upload a document. ",
     "Drag and drop a PDF. Show status: Uploading -> Processing -> Complete. Explain: extracted, chunked, embedded, indexed."),
    ("Step 3: Ask a question. ",
     "Type a question and submit. Point out real-time streaming, source citations with [Source N], expandable citation panel."),
    ("Step 4: Multi-document query. ",
     "Select 2-3 documents in sidebar. Ask a comparison question. Show response cites multiple documents separately."),
    ("Step 5: Semantic Search. ",
     "Switch to Search tab. Type a query. Show results with document name, score, page number, preview."),
    ("Step 6: API Documentation. ",
     "Open http://localhost:8000/docs. Show 18 interactive endpoints. Explain OpenAPI/Swagger auto-generation."),
    ("Step 7: Docker Infrastructure. ",
     "Show terminal: docker compose ps. Four containers running with health checks."),
]
for bold, text in demo_steps:
    pdf.bullet(text, bold_prefix=bold)

pdf.ln(3)
pdf.sub_heading("Demo Checklist (verify before presenting)")
checklist = [
    "Docker containers all running: docker compose ps",
    "Backend health: curl http://localhost:8000/api/v1/health",
    "Frontend loads at http://localhost:3000",
    "2-3 documents uploaded and processed",
    "Test a chat query to warm up the embedding model",
    "Have a sample PDF ready for live upload",
    "Browser in clean state (no console errors)",
]
for item in checklist:
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_GRAY)
    pdf.cell(5, 5.5, "[ ]")  # checkbox
    pdf.multi_cell(0, 5.5, " " + item)

# ── SLIDE 9 : CHALLENGES ────────────────────────────────────
pdf.add_page()
pdf.current_slide = 9
pdf.section_title("Engineering Challenges I Solved", "[5 minutes]")

pdf.speaker_note(
    "SAY: \"Building this system wasn't straightforward. I ran into real engineering problems "
    "that required creative solutions. I think problem-solving ability is what separates a "
    "junior developer from someone who can actually build production systems.\""
)

challenges = [
    ("Challenge 1: Null Bytes in PDF Extraction",
     "Problem: Academic PDFs produce text with null bytes (\\x00) from math symbols. PostgreSQL TEXT columns reject null bytes, causing 500 errors on upload.",
     "Solution: Built a text sanitization layer that strips null bytes and control characters while preserving Unicode. Runs on all extracted text before storage."),
    ("Challenge 2: Streaming Database Consistency",
     "Problem: FastAPI's dependency injection commits the DB session when the endpoint returns. But with streaming, the generator outlives the endpoint, so the assistant message was committed before it existed.",
     "Solution: Pre-commit session and user message before streaming starts. Use a fresh database session inside the generator for the assistant message."),
    ("Challenge 3: Ephemeral BM25 Index",
     "Problem: BM25 keyword index is in-memory only. Empty after every container restart. Hybrid search degraded to vector-only.",
     "Solution: Added startup hook that rebuilds BM25 index from all document chunks in PostgreSQL. Takes <1 second for thousands of chunks."),
    ("Challenge 4: Cross-Database Type Compatibility",
     "Problem: Models used PostgreSQL types (UUID, JSONB, ARRAY) but tests needed SQLite for speed.",
     "Solution: Built custom TypeDecorator classes (GUID, JSONType, ArrayType) that auto-detect dialect. PostgreSQL uses native types, SQLite uses portable alternatives. 103 tests run in 7.7s."),
    ("Challenge 5: Frontend Streaming Error Recovery",
     "Problem: Original streaming used fire-and-forget fetch().then(). Errors silently swallowed. UI got permanently stuck in loading state.",
     "Solution: Rewrote as proper async/await with AbortController timeout, HTTP status checking, error propagation, and fallback to non-streaming mode."),
]

for title, problem, solution in challenges:
    pdf.page_break_if_needed(45)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(180, 60, 60)
    pdf.set_x(10)
    pdf.multi_cell(pdf.w - 20, 5, problem)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 120, 60)
    pdf.set_x(10)
    pdf.multi_cell(pdf.w - 20, 5, solution)
    pdf.ln(3)

# ── SLIDE 10 : TESTING ──────────────────────────────────────
pdf.add_page()
pdf.current_slide = 10
pdf.section_title("Testing & Quality Assurance", "[2 minutes]")

pdf.body("Production-ready code needs production-ready testing. 103 automated tests across multiple layers:")

test_categories = [
    ("RAG Pipeline Tests - ",
     "Reciprocal Rank Fusion scoring, context building, message construction, source extraction. Edge cases: empty results, single source, score normalization."),
    ("Multi-Agent Tests - ",
     "State management, retrieval strategy selection, rank fusion scoring, edge cases for each agent."),
    ("Ingestion Pipeline Tests - ",
     "File extension mapping, content hashing, filename extraction, chunk boundary detection."),
    ("Integration Tests - ",
     "Session CRUD, health endpoint, metrics endpoint, end-to-end chat flow."),
    ("Load Tests (Locust) - ",
     "User behavior profiles simulating realistic usage: uploads, questions, searches under concurrent load."),
]
for bold, text in test_categories:
    pdf.bullet(text, bold_prefix=bold)

pdf.ln(3)
pdf.body(
    "All tests run in 7.7 seconds on SQLite backend - fast enough for CI/CD on every commit. "
    "Alembic migrations provide version-controlled schema changes for production deployments."
)

# ── SLIDE 11 : METRICS ──────────────────────────────────────
pdf.add_page()
pdf.current_slide = 11
pdf.section_title("Project Metrics & Achievements", "[2 minutes]")

# Stats grid
metrics = [
    ("Source Files", "99"),
    ("Lines of Code", "6,700+"),
    ("Python Modules", "49"),
    ("React Components", "20"),
    ("API Endpoints", "18"),
    ("AI Agents", "5"),
    ("Automated Tests", "103"),
    ("Docker Services", "4"),
]
y_start = pdf.get_y() + 2
col = 0
for label, value in metrics:
    x = 12 + (col * 48)
    pdf.set_xy(x, y_start)
    pdf.stat_box(label, value)
    col += 1
    if col >= 4:
        col = 0
        y_start += 28

pdf.set_y(y_start + 30)

pdf.sub_heading("Key Features Delivered")
features = [
    "Hybrid search combining dense (vector) and sparse (BM25) retrieval with RRF",
    "Five-agent pipeline with self-improving reflection loop",
    "Real-time token streaming via Server-Sent Events",
    "Multi-format document ingestion (PDF, DOCX, TXT, images)",
    "Cross-database type compatibility layer (PostgreSQL + SQLite)",
    "Structured logging, Prometheus metrics, rate limiting, security headers",
    "Dark mode UI with responsive design and conversation export",
]
for f in features:
    pdf.bullet(f)

# ── SLIDE 12 : CONCEPTS ─────────────────────────────────────
pdf.add_page()
pdf.current_slide = 12
pdf.section_title("Key Concepts I Mastered", "[3 minutes]")

concept_groups = [
    ("1. Retrieval-Augmented Generation (RAG)", [
        "Document ingestion pipelines with multi-format extraction",
        "Semantic chunking with heading detection and sentence-boundary overlap",
        "Embedding generation with SentenceTransformers",
        "Vector storage and similarity search with Pinecone",
        "Context enrichment and citation generation",
    ]),
    ("2. Agentic AI Architecture", [
        "Multi-agent systems with specialized roles",
        "State machine orchestration patterns",
        "Self-improving loops with reflection and revision",
        "Separation of concerns in AI pipeline design",
    ]),
    ("3. Full-Stack Engineering", [
        "Async Python: FastAPI, SQLAlchemy 2.0, asyncpg",
        "React 18 with TypeScript, Zustand, TanStack Query",
        "Real-time streaming with Server-Sent Events",
        "RESTful API design with validation and proper status codes",
    ]),
    ("4. Data Engineering", [
        "Hybrid search: dense + sparse retrieval with RRF",
        "Vector database management with Pinecone",
        "PostgreSQL async ORM with cross-database compatibility",
    ]),
    ("5. DevOps & Production Readiness", [
        "Docker Compose multi-service orchestration",
        "Database migrations, health checks, rate limiting",
        "Prometheus metrics and structured logging",
        "Comprehensive automated testing (103 tests)",
    ]),
    ("6. Problem Solving", [
        "Debugging production issues: null bytes, streaming consistency, memory management",
        "Designing for resilience: timeouts, error recovery, graceful degradation",
        "Performance optimization: lazy loading, batch processing, caching",
    ]),
]

for group_title, items in concept_groups:
    pdf.page_break_if_needed(30)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 7, group_title, new_x="LMARGIN", new_y="NEXT")
    for item in items:
        pdf.bullet(item, indent=4)
    pdf.ln(1)

# ── SLIDE 13 : DIFFERENTIATOR ───────────────────────────────
pdf.add_page()
pdf.current_slide = 13
pdf.section_title("What Makes This Different", "[2 minutes]")

pdf.speaker_note(
    "SAY: \"I want to address why this project stands out compared to other portfolio projects you might see.\""
)

diffs = [
    ("Production-grade, not proof-of-concept. ",
     "Error handling, input validation, rate limiting, security headers, structured logging, "
     "metrics, health checks, automated tests. Most portfolio RAG projects skip all of this."),
    ("Complete system. ",
     "Frontend, backend, database, vector store, search index, AI pipeline, agents, testing, "
     "Docker. The full picture, not just an API."),
    ("Real engineering problems solved. ",
     "Null bytes, streaming DB consistency, BM25 persistence, cross-database compatibility. "
     "These are production problems solved with proper engineering, not hacks."),
    ("Theory understood, not just applied. ",
     "I can explain why RRF works, why hybrid search outperforms single-strategy, why multi-agent "
     "produces better results than single-prompt, and why each architectural decision was made."),
]
for bold, text in diffs:
    pdf.bullet(text, bold_prefix=bold)
    pdf.ln(1)

pdf.ln(4)
pdf.set_font("Helvetica", "B", 12)
pdf.set_text_color(*NAVY)
pdf.set_x(10)
pdf.multi_cell(pdf.w - 20, 7,
    "This project demonstrates that I can take an ambiguous, complex problem and deliver "
    "a working, well-architected, production-ready solution.", align="C")

# ── SLIDE 14 : FUTURE + Q&A ─────────────────────────────────
pdf.add_page()
pdf.current_slide = 14
pdf.section_title("Future Roadmap", "[1 minute]")

future = [
    "Kubernetes deployment with horizontal pod autoscaling",
    "OAuth 2.0 / SSO authentication",
    "WebSocket support for bi-directional real-time communication",
    "Multi-modal RAG - processing images and charts within documents",
    "Fine-tuned embedding model on domain-specific data",
    "CI/CD pipeline with GitHub Actions",
    "Response caching and adaptive model selection for cost optimization",
]
for f in future:
    pdf.bullet(f)

pdf.ln(6)
pdf.section_title("Q&A Preparation", "")

qa = [
    ("Q: Why Claude over GPT-4?",
     "Excellent citation following, generous context window, clean streaming API. Designed with abstraction layer - swapping models requires changing one file."),
    ("Q: How would you scale this?",
     "Kubernetes for horizontal scaling, managed PostgreSQL (RDS), Pinecone auto-scales, Redis caching, BM25 moves to Elasticsearch."),
    ("Q: Hardest bug?",
     "Streaming DB consistency. FastAPI dependency injection lifecycle interacting with async generators required pre-committing and fresh sessions."),
    ("Q: Why not LangChain?",
     "Built from scratch to demonstrate understanding of underlying patterns. Full control, easier debugging. Would evaluate LangChain based on team needs."),
    ("Q: Latency?",
     "Non-streaming: 3-5s. Streaming first token: <2s. Upload+embed: 1-2s small, 15-20s large PDFs. Bottleneck is Claude API, not infrastructure."),
]
for question, answer in qa:
    pdf.page_break_if_needed(25)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.set_x(10)
    pdf.multi_cell(pdf.w - 20, 5, question)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_GRAY)
    pdf.set_x(10)
    pdf.multi_cell(pdf.w - 20, 5, answer)
    pdf.ln(2)

# ── CLOSING PAGE ─────────────────────────────────────────────
pdf.add_page()
pdf.current_slide = 15

# Navy block
pdf.set_fill_color(*NAVY)
pdf.rect(0, 0, 210, 297, "F")

pdf.set_y(80)
pdf.set_font("Helvetica", "B", 28)
pdf.set_text_color(*WHITE)
pdf.cell(0, 12, "Thank You", align="C", new_x="LMARGIN", new_y="NEXT")

pdf.ln(4)
pdf.set_draw_color(*BLUE)
pdf.set_line_width(1)
pdf.line(70, pdf.get_y(), 140, pdf.get_y())
pdf.ln(8)

pdf.set_font("Helvetica", "", 14)
pdf.set_text_color(148, 163, 184)
pdf.cell(0, 8, "IntelliDoc Nexus", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Multi-Agent RAG-Powered Document Intelligence", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(15)

pdf.set_font("Helvetica", "", 12)
pdf.set_text_color(*WHITE)
pdf.cell(0, 8, "[YOUR NAME]", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "[YOUR EMAIL]", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "[YOUR LINKEDIN / GITHUB]", align="C", new_x="LMARGIN", new_y="NEXT")

pdf.ln(20)
pdf.set_font("Helvetica", "I", 11)
pdf.set_text_color(148, 163, 184)
pdf.cell(0, 8, "\"I'm happy to answer any questions -", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "and I can dive into any part of the codebase live right now.\"", align="C", new_x="LMARGIN", new_y="NEXT")


# ══════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════
output_path = "/Users/nagavenkatasaichennu/Desktop/project-1/intellidoc-nexus/IntelliDoc_Nexus_Presentation.pdf"
pdf.output(output_path)
print(f"PDF generated: {output_path}")
print(f"Pages: {pdf.page_no()}")
