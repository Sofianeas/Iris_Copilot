# 🤖 IRIS Copilot
# AI ENGINEERING GUIDE
Version : 1.0

---

# Purpose

This document defines how AI assistants (ChatGPT, Claude, Gemini or future coding assistants) must contribute to the IRIS Copilot project.

Its objective is to guarantee:

- architectural consistency;
- maintainable code;
- predictable implementations;
- reusable components;
- high software quality.

Every AI contribution must comply with this document.

---

# AI Philosophy

Artificial Intelligence is considered a software engineering assistant.

It helps develop the application.

It never replaces architectural decisions.

Important decisions always remain under human control.

---

# AI Responsibilities

AI assistants may:

- generate code;
- refactor existing modules;
- optimize algorithms;
- propose improvements;
- create documentation;
- generate tests;
- generate UI components.

AI assistants must never modify the project architecture without explicit validation.

---

# Project Vision

IRIS Copilot is NOT a demo project.

It is a professional software platform designed for daily HelpDesk operations.

Every implementation should prioritize:

- maintainability;
- readability;
- modularity;
- scalability;
- user experience.

---

# Engineering Principles

Always prefer:

✔ Simple solutions

✔ Explicit code

✔ Reusable modules

✔ Small functions

✔ Clear architecture

Never optimize prematurely.

Never over-engineer.

---

# Layer Responsibilities

The application is divided into independent layers.

UI

↓

Pages

↓

Services

↓

Agents

↓

Models

↓

Database

↓

External APIs

No layer should bypass another layer.

---

# Streamlit Rules

Pages only orchestrate.

Pages never contain business logic.

Pages never access SQLite directly.

Pages never access ChromaDB directly.

Pages never call Gemini directly.

Instead:

Pages

↓

Services

↓

Agents

↓

Database

---

# UI Rules

All graphical components belong to:

app/ui/

Never duplicate UI code.

Never duplicate CSS.

Always reuse existing components.

Whenever a new reusable component is needed:

Create it once.

Reuse it everywhere.

---

# CSS Rules

Official stylesheet:

app/ui/styles.css

Never copy CSS into multiple pages.

Avoid inline CSS.

Prefer reusable classes.

---

# Service Rules

Each service has exactly one responsibility.

Example:

parser_service.py

↓

Mail parsing

router_service.py

↓

Agent selection

db_service.py

↓

SQLite

vectorstore_service.py

↓

ChromaDB

memory_service.py

↓

Knowledge memory

Services should remain independent whenever possible.

---

# Agent Rules

Each client owns one dedicated agent.

Never merge multiple clients into a generic agent.

Never hardcode client-specific rules outside the agent.

---

# Memory Rules

IRIS Copilot includes several memories.

Documentation Memory

↓

Ticket Memory

↓

Correction Memory

↓

Learning Reports

Memory is observational.

Memory never changes business rules automatically.

---

# AI Safety Rules

AI assistants must NEVER:

invent business procedures;

invent customer-specific rules;

invent ticket fields;

invent mandatory information.

If information is missing:

Return uncertainty.

Ask for clarification.

Never fabricate.

---

# Human Validation

Every AI-generated ticket must be editable.

Users always remain in control.

No automatic submission.

No automatic rule changes.

---

# Traceability

Every AI interaction should be traceable.

Whenever possible, record:

- timestamp
- agent
- prompt version
- documents retrieved
- model version
- user corrections

Transparency is mandatory.

---

# Documentation Rules

Every new feature must update:

Architecture

Roadmap

Changelog

Relevant documentation

Documentation is part of development.

---

# Code Quality

Preferred characteristics:

Readable

Small

Typed

Documented

Modular

Avoid:

Huge files

Duplicate code

Nested logic

Global state

Hidden side effects

---

# File Size Guidelines

Recommended maximum sizes:

Streamlit page

≈ 250 lines

Service

≈ 300 lines

Component

≈ 200 lines

Function

≈ 40 lines

Longer implementations should be split.

---

# Error Handling

Never ignore exceptions.

Never use:

except:
    pass

Instead:

- catch specific exceptions;
- log them;
- provide useful feedback.

---

# Logging

Important operations must be logged.

Examples:

mail received

agent selected

Gemini request

SQLite save

VectorStore update

Memory update

Errors

---

# Performance

Prefer:

cache

lazy loading

shared resources

resource reuse

Avoid unnecessary LLM calls.

---

# RAG Rules

Documentation must always come from indexed documents.

Never invent documentation.

When available, indicate:

- source document
- document section
- confidence

---

# Prompt Engineering

Prompts should:

be versioned;

be documented;

remain deterministic whenever possible.

Prompt changes should be recorded.

---

# Testing

Every important service should be testable independently.

AI-generated code should avoid tight coupling with Streamlit.

---

# Git Workflow

Recommended workflow:

Feature

↓

Development

↓

Review

↓

Testing

↓

Documentation

↓

Commit

↓

Merge

Never merge undocumented code.

---

# Collaboration Between AI Assistants

Current recommended workflow:

Claude

- feature implementation
- service generation
- agent generation
- automation

ChatGPT

- architecture
- engineering decisions
- UI/UX
- optimization
- code review
- roadmap
- documentation

Both assistants should respect the same architecture.

---

# Review Checklist

Before considering a feature complete:

☐ Architecture respected

☐ No duplicated code

☐ Services isolated

☐ UI reusable

☐ Logging implemented

☐ Errors handled

☐ Documentation updated

☐ Tests executed when applicable

☐ Business rules respected

☐ Human validation preserved

---

# Definition of Done

A feature is considered complete only if:

- it works;
- it follows the architecture;
- it is documented;
- it is maintainable;
- it is reusable;
- it respects AI safety principles.

---

# Long-Term Vision

IRIS Copilot should progressively evolve into an intelligent HelpDesk platform capable of:

- understanding customer requests;
- retrieving relevant documentation;
- generating high-quality tickets;
- remembering previous validated cases;
- assisting consultants without replacing them.

The objective is not autonomous decision-making.

The objective is augmented human expertise.

---

# Project Motto

> Build software that consultants trust.

Not software that merely produces answers.