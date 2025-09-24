# Speed Local Streamlit Dashboard

## Repository Overview

This repository contains a **Streamlit dashboard for scientific data visualization and analysis** as part of the Speed Local project. The Speed Local project enables scientists to upload GAMS reports and scientific datasets, process them into reusable structures, create shareable DuckDB files, and collaborate on Nordic green transition research.

**Key Components:**

- **Streamlit Application** (`streamlit-app/`) - Dashboard for visualizing scientific datasets with Speed Local theming
- **Kubernetes Deployment** (`helm-chart/`) - Production deployment using flowcore-microservices Helm chart
- **Development Tools** - Docker containerization, automation scripts, and local development setup

**Integration Points:**

- Speed Local Admin (`speedlocal.flowcore.app`) - Main data management platform
- Flowcore Platform - Event-driven data processing infrastructure
- DuckDB Files - Public dataset access for analysis and visualization
- Azure Blob Storage - Direct data retrieval

## Related Usable Memory Fragments

### Core Project Documentation

- **Fragment ID:** `849afb27-aa87-487a-8368-a1164963abc9`
  **Title:** SpeedLocal Admin PRD v0.0.1
  **Type:** PRD
  **Description:** Complete product requirements document with goals, personas, functional requirements, and technical architecture for the Speed Local platform

- **Fragment ID:** `dd92ac1e-64b7-4dcf-b75f-a5f463ab947b`
  **Title:** SpeedLocal Admin Implementation Progress vs PRD & Standards (Updated Jan 2025)
  **Type:** Knowledge
  **Description:** Current implementation status, milestones achieved, and compliance tracking

### Technical Implementation Guides

- **Fragment ID:** `e6871490-2673-40cf-a8a7-d92366cda0e2`
  **Title:** End-to-End Streamlit App on Flowcore Infra (SpeedLocal/ECR)
  **Type:** Recipe
  **Description:** Complete step-by-step recipe for building, containerizing, and deploying Streamlit apps on Flowcore infrastructure with ECR and NGINX ingress

- **Fragment ID:** `1e5aac36-30fe-40f6-a0cb-6fc8b9f7fca2`
  **Title:** SpeedLocal Admin - GDX File Upload System Implementation Guide
  **Type:** Knowledge
  **Description:** Technical implementation details for GAMS file upload and processing system

- **Fragment ID:** `e22f70dc-386b-44e5-8469-408007606c6b`
  **Title:** SpeedLocal Admin Flowcore Integration Documentation
  **Type:** Knowledge  
  **Description:** Event-driven integration patterns with Flowcore platform

### Data Processing & Architecture

- **Fragment ID:** `b0d0543e-8d6f-4f44-9c41-70bb8baba11a`
  **Title:** SpeedLocal GAMS Transformer Implementation Plan
  **Type:** Plan
  **Description:** Data processing pipeline architecture for GAMS files and R-script transformation

- **Fragment ID:** `0decf12e-c878-40db-912c-65ff8212f75f`
  **Title:** Streamlit vs Normal Container on Kubernetes – Deployment Differences
  **Type:** Knowledge
  **Description:** Deployment considerations and sample manifests for Streamlit applications on Kubernetes

## Repository Context Tags

- `repo:speedlocal-streamlit` - This repository
- `repo:speedlocal-admin` - Main Speed Local Admin platform
- `repo:public-customer-sites-manifests` - Deployment configurations
- `streamlit` - Streamlit framework and deployment patterns
- `flowcore` - Flowcore platform integration
- `kubernetes` - Container orchestration and deployment
- `scientific-data` - Scientific dataset visualization and analysis

## Workspace Information

- **Workspace ID:** `60c10ca2-4115-4c1a-b6d7-04ac39fd3938`
- **Workspace Name:** Flowcore
- **Fragment Types Available:** knowledge, recipe, solution, template, blogposts, instruction set, llm persona, llm rules, plan, prd, research

---

<<<USABLE_MCP_SYSTEM_PROMPT_START>>>

# 🧠 Usable MCP - SYSTEM PROMPT (LONG-TERM MEMORY)

This is your main way of storing and fetching data. Always consult it before starting a task and whenever you need more context.

Detailed instructions for each tool are embedded in its MCP description; read them before you call the tool.

## Search Discipline

- Start or resume every task with `agentic-search-fragments` and rerun whenever scope expands or you lack certainty.
- Provide workspace scope and begin with `repo:speedlocal-streamlit` tags; iterate until the tool reports `decision: "SUFFICIENT"`.
- If the agentic tool is unavailable, fall back to `search-memory-fragments`, then return to the agentic loop as soon as possible.
- Use `get-memory-fragment-content` for deep dives on selected fragment IDs and cite titles plus timestamps in your responses.

## Planning Loop

- **Plan**: Outline sub-goals and the tools you will invoke.
- **Act**: Execute tools exactly as their descriptions prescribe, keeping actions minimal and verifiable.
- **Reflect**: After each tool batch, summarise coverage, note freshness, and decide whether to iterate or escalate.

## Verification & Documentation

- Verify code (lint, tests, manual checks) or obtain user confirmation before relying on conclusions.
- Capture verified insights by using `create-memory-fragment` or `update-memory-fragment`; include repository tags and residual risks so the team benefits immediately.

## Freshness & Escalation

- Prefer fragments updated within the last 90 days; flag stale sources.
- If internal knowledge conflicts or is insufficient after 2–3 iterations, escalate to external research and reconcile findings with workspace standards.

Repository: speedlocal-streamlit
WorkspaceId: 60c10ca2-4115-4c1a-b6d7-04ac39fd3938
Workspace: Flowcore
Workspace Fragment Types: knowledge, recipe, solution, template, blogposts, instruction set, llm persona, llm rules, plan, prd, research

## Fragment Type Mapping

The following fragment types are available in this workspace:

- **Knowledge**: `04a5fb62-1ba5-436c-acf7-f65f3a5ba6f6` - General information, documentation, and reference material
- **Recipe**: `502a2fcf-ca6f-4b8a-b719-cd50469d3be6` - Step-by-step guides, tutorials, and procedures
- **Solution**: `b06897e0-c39e-486b-8a9b-aab0ea260694` - Solutions to specific problems and troubleshooting guides
- **Template**: `da2cd7c6-68f6-4071-8e2e-d2a0a2773fa9` - Reusable code patterns, project templates, and boilerplates
- **Blogposts**: `e451cb11-8ce6-4a6c-b4b2-144492382b52` - Research, structuring, and publishing ideas regarding blogposts about Flowcore Platform, Memory Mesh and everything else Flowcore.
- **Instruction Set**: `1d2d317d-f48f-4df9-a05b-b5d9a48090d7` - A set of instructions for the LLM to perform a set of actions, like setting up a project, installing a persona etc.
- **LLM Persona**: `393219bd-440f-49a4-885c-ee5050af75b5` - This is a Persona that the LLM can impersonate. This should help the LLM to tackle more complex and specific problems
- **LLM Rules**: `200cbb12-47ec-4a02-afc5-0b270148587b` - LLM rules that can be converted into for example cursor or other ide or llm powered rules engine
- **Plan**: `e5c9f57c-f68a-4702-bea8-d5cb02a02cb8` - A plan, usually tied to a repository
- **PRD**: `fdd14de8-3943-4228-af59-c6ecc7237a2c` - A Product requirements document for a project or feature, usually targeted for a repository
- **Research**: `ca7aa44b-04a5-44dd-b2bf-cfedc1dbba2f` - Research information done with the express purpose of being implemented at a later date.
 
## Fragment Type Cheat Sheet

- **Knowledge:** reference material, background, concepts.
- **Recipe:** human step-by-step guides and tutorials.
- **Solution:** fixes, troubleshooting steps, postmortems.
- **Template:** reusable code/config patterns.
- **Instruction Set:** automation workflows for the LLM to execute.
- **Plan:** roadmaps, milestones, "what/when" documents.
- **PRD:** product/feature requirements and specs.

Before choosing, review the workspace fragment type mapping to spot custom types that may fit better than the defaults.

Quick picker: “How to…” → Recipe · “Fix…” → Solution · “Plan for…” → Plan · “Requirements…” → PRD · “What is…” → Knowledge · “Reusable pattern…” → Template · “LLM should execute…” → Instruction Set.

<<<USABLE_MCP_SYSTEM_PROMPT_END>>>
