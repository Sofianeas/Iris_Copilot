# IRIS Copilot

> **Prototype / Work in Progress — Not production-ready**

IRIS Copilot is an experimental application framework designed to explore how AI-assisted workflows could support IT Help Desk activities.

The project is being developed progressively with a strong focus on **software architecture, maintainability, user experience and AI integration**.

The current repository represents an **active development state**. It should therefore be considered a **prototype / engineering workbench**, not a finished product.

---

## ⚠️ Project Status

**Status: Work in Progress**

IRIS Copilot is **not currently intended for production deployment**.

The repository is shared primarily to make the current development work, architecture and technical direction visible.

Some components are already implemented and others are still under development, refactoring or architectural validation.

Therefore:

* some features may be incomplete;
* some interfaces may change;
* some modules may not yet be fully integrated;
* some workflows may only be partially functional;
* the current implementation does not represent the final product;
* APIs, modules and internal structures may change during development.

> **Important:** A working development interface should not be interpreted as a production-ready application.

The application will only be considered deployable after the required functional, technical, security and validation steps have been completed.

---

# 🎯 Objectives

The long-term objective of IRIS Copilot is to provide a structured workspace for IT Help Desk activities, with the possibility of assisting technicians in repetitive and knowledge-intensive workflows.

The project is intended to progressively explore capabilities such as:

* analysis of incoming support requests;
* assistance with ticket preparation;
* access to technical documentation;
* historical information retrieval;
* AI-assisted workflows;
* structured interaction between application services and AI agents.

The project originates from a real Help Desk environment where support requests are received through professional mailboxes and subsequently processed as tickets in the operational ticketing system.

The purpose of the project is **not to automate the Help Desk blindly**, but to investigate how an assistant can support technicians while keeping the human operator in control.

---

# 🏗️ Architecture

The project is being developed around a layered architecture intended to keep the user interface, application framework, business services and AI capabilities loosely coupled.

The target architecture can be summarized as:

```text
                         IRIS Copilot
                              │
                              ▼
                     ┌─────────────────┐
                     │   Application   │
                     │      Shell      │
                     └────────┬────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
        Presentation      Application       Session
            / UI          Framework          State
             │                │                │
             └────────────────┼────────────────┘
                              │
                              ▼
                         Services
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
            Business Logic           External APIs
                 │
                 ▼
                         AI Interfaces
                              │
                              ▼
                     AI Agents / LLMs
```

The architecture is intentionally designed to avoid coupling the application directly to a specific LLM provider.

The application should interact with AI capabilities through defined interfaces rather than depending directly on a particular model or vendor.

---

# 🧩 Current Development Structure

The project is being developed through several architectural areas.

## UI / Design System

The first development stage established the foundation of the user interface.

The following components have been developed and considered stable at the current stage:

* Theme
* Typography
* Layout
* Cards
* Badges
* Alerts
* Metrics
* Tables
* Timeline
* Navigation
* Sidebar
* Forms
* Icons
* Public UI API
* Living Style Guide

The Design System is intended to remain stable and should only evolve through explicit architectural decisions or bug fixes.

---

## Application Framework

The current development direction is focused on building the application's structural foundation before continuing with extensive business functionality.

The Phase 2 roadmap includes:

### AF-001 — Application Framework Architecture

Definition of:

* logical architecture;
* execution flows;
* module responsibilities;
* interfaces between layers;
* architectural principles.

This stage is intended to establish the technical reference architecture before further implementation.

### AF-002 — Application Shell

The Shell is intended to provide the structural backbone of the application.

Its responsibilities include:

* application initialization;
* global application structure;
* orchestration of common components;
* integration with `main.py`.

The Shell must **not contain business logic**.

### AF-003 — Session

A dedicated session layer is planned to centralize access to `st.session_state`.

The objective is to prevent individual pages from directly managing global application state.

### AF-004 — Navigation

Navigation is being designed as a centralized and extensible component independent from business pages.

Adding a page should ultimately require only a configuration-level change.

### AF-005 — Global Layout

The application will progressively converge toward a shared structure:

```text
┌──────────────────────────────────────┐
│ Header                               │
├───────────────┬──────────────────────┤
│ Sidebar       │                      │
│               │      Workspace       │
│               │                      │
├───────────────┴──────────────────────┤
│ Footer (optional)                    │
└──────────────────────────────────────┘
```

This provides a consistent structure across application pages.

---

# 📊 Planned Application Pages

The application currently revolves around several functional areas that are being progressively reorganized.

The planned structure includes modules such as:

```text
IRIS Copilot
│
├── Dashboard
│
├── Mail Analysis
│
├── Documentation
│
├── Ticket Generation
│
└── History
```

The corresponding modules currently include:

```text
analyse_mail.py
documentation.py
generation_ticket.py
historique.py
```

These pages are intended to be progressively refactored once the application framework and Shell have been stabilized.

---

# 🤖 AI Architecture

The AI layer is being developed as a separate concern from the core application framework.

This separation is intentional.

The project currently distinguishes between two major development areas:

### Application & Architecture

Focus:

* UI;
* Design System;
* application framework;
* Shell;
* navigation;
* page architecture;
* UX;
* maintainability.

### AI / Agents

Focus:

* agent architecture;
* orchestration;
* prompts;
* AI workflows;
* memory;
* RAG;
* document pipelines;
* mail analysis;
* ticket generation;
* future specialized agents.

This separation allows both areas to evolve independently while communicating through explicit interfaces.

---

# 🧠 Development Methodology

Development follows a deliberate engineering cycle rather than feature development without architectural review.

Each significant development step follows:

```text
Audit
  ↓
Analysis
  ↓
Plan
  ↓
Implementation
  ↓
Validation
  ↓
Recommendations
```

### 1. Audit

Understand the current state of the project.

### 2. Analysis

Identify architectural, functional or technical gaps.

### 3. Plan

Define the modifications before implementation.

### 4. Implementation

Implement one category of changes at a time.

### 5. Validation

Verify functionality, architecture and consistency.

### 6. Recommendations

Identify improvements and prepare the next development step.

This methodology is intended to prevent uncontrolled technical debt and preserve architectural consistency throughout the project.

---

# 🔐 Architectural Principles

The project follows several principles intended to remain valid throughout future development.

### Single Responsibility

Each module should have one clearly defined responsibility.

### UI / Business Separation

The Design System must remain independent from business concepts such as tickets, emails or AI agents.

### Pages Orchestrate, Services Execute

Pages are responsible for the user interface and orchestration.

Business logic should be delegated to dedicated services.

### Loose Coupling with AI

The application should not depend directly on a specific LLM provider.

AI capabilities should be accessed through defined interfaces.

### Extensibility

New functionality should be introduced without modifying the foundations of the application whenever possible.

These principles form part of the architectural direction for the Application Framework.

---

# 🚀 Running the Project Locally

> **Note:** The exact installation and execution procedure may evolve while the project is under development.

## Requirements

Recommended environment:

* Python 3.x
* Git
* a Python virtual environment
* the dependencies listed in `requirements.txt`, if present

---

## 1. Clone the repository

```bash
git clone https://github.com/Sofianeas/Iris_Copilot.git
cd Iris_Copilot
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install dependencies

If the repository contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

---

## 4. Start the application

If the application entry point is `main.py` and the project is executed with Streamlit:

```bash
streamlit run main.py
```

The application should then be available through the local Streamlit server.

> The execution command should be considered provisional until the application framework and deployment architecture are finalized.

---

# 📁 Repository Structure

The repository is organized around the application source code, UI components and progressive architectural work.

A simplified conceptual structure is:

```text
Iris_Copilot/
│
├── main.py
│
├── analyse_mail.py
├── documentation.py
├── generation_ticket.py
├── historique.py
│
├── app/
│   ├── ui/
│   ├── shell/
│   ├── session/
│   └── ...
│
├── requirements.txt
│
└── README.md
```

> The structure above represents the intended architectural organization. Individual directories and modules may still evolve during development.

---

# 🧪 Current Limitations

This repository should **not** currently be treated as a production deployment package.

Known limitations include:

* ongoing architectural changes;
* incomplete integration between modules;
* evolving application framework;
* incomplete AI workflows;
* APIs and internal interfaces that may change;
* absence of final production validation;
* deployment architecture not yet frozen.

The current state is therefore primarily useful for:

* technical review;
* architectural discussion;
* development follow-up;
* experimentation;
* demonstration of the current progress.

---

# 🗺️ Roadmap

The current roadmap is focused on stabilizing the application framework before expanding the business functionality.

```text
Phase 1 — UI Foundation
        │
        │  Completed / Stabilized
        ▼
Phase 2 — Application Framework
        │
        ├── AF-001 Architecture
        ├── AF-002 Shell
        ├── AF-003 Session
        ├── AF-004 Navigation
        ├── AF-005 Global Layout
        ├── AF-006 Dashboard
        └── AF-007 Page Conventions
        │
        ▼
Phase 3 — Business Pages
        │
        ├── Mail Analysis
        ├── Documentation
        ├── Ticket Generation
        └── History
        │
        ▼
AI / Agents
        │
        ├── Agent architecture
        ├── Orchestration
        ├── RAG
        ├── Memory
        └── Specialized workflows
        │
        ▼
Production Validation
        │
        ├── Functional validation
        ├── Technical validation
        ├── Security review
        ├── Performance
        ├── Deployment
        └── Operational monitoring
```

The roadmap is deliberately progressive: infrastructure and architectural foundations are established before large-scale business functionality is added.

---

# 👥 Development Roles

The project currently follows a collaborative development model.

### Product Owner / Final Decision Maker

Responsible for:

* functional requirements;
* roadmap;
* final technical and functional decisions;
* testing;
* validation;
* integration decisions.

### Software Architecture

Responsible for:

* application architecture;
* UI architecture;
* Design System;
* code quality;
* maintainability;
* architectural consistency.

### AI / Agents

Responsible for:

* AI architecture;
* agents;
* orchestration;
* prompts;
* RAG;
* AI workflows;
* future AI capabilities.

No significant architectural change should be integrated without validation.

---

# ⚠️ Production Disclaimer

IRIS Copilot is currently an **engineering prototype under active development**.

The presence of a runnable interface does **not** imply that the application is ready for operational use.

Before any production deployment, the project will require additional validation covering at least:

* functional correctness;
* architecture;
* security;
* authentication and authorization;
* data protection;
* error handling;
* logging and monitoring;
* performance;
* dependency management;
* deployment procedures;
* rollback procedures;
* operational documentation.

Until these conditions have been addressed, the repository should be considered a **development and demonstration environment only**.

---

# 📌 Why This Repository Is Public

The repository is made available to facilitate:

* visibility into the development process;
* architectural review;
* technical discussion;
* collaboration;
* feedback from software development and R&D teams.

The objective is to expose the **current engineering direction and progress**, rather than to present IRIS Copilot as a finished product.

---

# 📄 License

See the repository license file for the applicable terms.

---

## Current Status

**IRIS Copilot — Work in Progress**

The project is actively evolving.

**Not production-ready.
Not intended for deployment in its current state.
Architecture and implementation are subject to change.**
