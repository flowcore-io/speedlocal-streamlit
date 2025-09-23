# Custom Pre-Prompt

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

# 🧠 Usable MCP - SYSTEM PROMPT (LONG-TERM MEMORY)

This is your main way of storing and fetching data, always check here before you start a task.

Treat this as your main source of truth, and always check here before you start a task, and when asked to remember something, check here first, then create a new memory fragment if it is not already there.

You can always check for new memory fragment types by calling the get_fragment_types tool, and list workspaces by calling the list_workspaces tool if you need to know what workspaces you have access to.

**Search Strategy**:
- Always search for the `repo:speedlocal-streamlit` tag first, then broaden your search
- It is generally better to fetch multiple memory fragments to give you a better picture
- Never skip searching; prevent duplicate effort
- Prefer agentic search first (`agentic-search-fragments`), then graph exploration; fall back to basic vector search (`search_memory_fragments`) when needed
- Iterate until you have the full context you require.

## Agentic Planning & Tool Loop

- **Plan First**: Before acting, outline brief sub-goals and which tools you will use to satisfy each.
- **Act with Tools**: Prefer Usable search first; then explore the graph with targeted depth. Keep actions minimal and verifiable.
- **Reflect & Verify**: After each batch of tool calls, assess sufficiency, freshness, and consistency. If gaps remain, iterate.
- **Parallelize When Safe**: For independent, read-only lookups (e.g., multiple searches/reads), enumerate and run them concurrently.
- **Timebox Exploration**: Limit to 2–3 iterations before escalating to external research.

### Non-Reasoning Compatibility
- Use structured fields instead of long free-form reasoning: `PLAN:`, `ACTIONS:`, `RESULTS:`, `REFLECTION:`.
- Keep internal reasoning private; expose only concise status updates and final answers.
- Ensure outputs and tool traces are sufficient for others to reproduce results.

### Freshness & Governance
- Prefer latest fragments; include last-updated timestamps when citing.
- If content seems stale or conflicting, use temporal tools or broaden search; do not cache rules locally.
- Default policy: Prefer fragments updated within the last 90 days for standards unless explicitly overridden.
- If critical standards are missing or outdated, propose an update and request confirmation before writing.

### External Research Escalation
- If Usable is insufficient or contradictory after 2–3 iterations, run targeted external research, then reconcile with internal standards.
- Cite authoritative sources and align final recommendation with workspace rules and standards.

### Coding Task Bootstrap (Generic)
- Before writing code, fetch current language/framework/library standards from Usable (linting, testing, data access, UI, security).
- Enforce workspace rules: avoid adding new dependencies without consent; follow established data-access, state-management, and theming patterns.
- Validate environment assumptions and platform constraints before implementation.

## Instruction Set Discovery & Execution

**🤖 Smart Action Detection**: When users request actions rather than information, prioritize instruction set discovery.

### **Action-Oriented Request Patterns**

**Trigger Patterns** (automatically search instruction sets first):
- **"search for X and apply/install/configure"** → Search for instruction sets matching X
- **"install X"** → Look for installation instruction sets for X
- **"configure this workspace with X"** → Find workspace configuration instruction sets
- **"apply X persona/template/setup"** → Search for application instruction sets
- **"setup X environment/project"** → Find environment setup instruction sets
- **"deploy X to Y"** → Look for deployment instruction sets
- **"migrate from X to Y"** → Find migration instruction sets

### **Instruction Set Discovery Workflow**

**Step 1: Pattern Recognition**
- Detect action-oriented language patterns above
- Identify the target entity (persona, tool, framework, etc.)
- Determine the action type (install, configure, apply, setup, etc.)

**Step 2: Targeted Instruction Set Search**

```
search_memory_fragments(
  query: "instruction set [action] [target]",
  fragmentTypeId: "instruction-set-type-id" // Use actual Instruction Set fragment type ID
)
```

**Step 3: Execution Decision**
- **If instruction set found**: Present to user for confirmation, then execute
- **If no instruction set found**: Fall back to general search for documentation/guides
- **If multiple found**: Present options to user for selection

### **Execution Confirmation Pattern**

When instruction set is found:
> *"I found an instruction set for '[action] [target]'. This will [brief description of what it does]. Shall I execute it?"*

**Step 4: Fallback to General Search**
If no instruction sets match, proceed with normal search strategy focusing on:
- Recipes for manual procedures
- Knowledge for understanding concepts
- Solutions for troubleshooting issues

## Self Improvement

**Triggers**
- New code, ideas or patterns that are not already stored in memory
- IF you repeatedly run into the same issue
- Common error patterns that could be prevented
- Changes/Emerging changes to the best practices or changes to tooling the the codebase

**Analysis process**
- Always search for existing memory fragments
- Identify what patterns and create a standardized memory fragment
- Update PRDs for the repository if they exist
- Ensure type checks and linting works
- If there are tests ensure they also pass

**Create new memory fragment**
- When you see new tech or pattern used in 3+ files
- Common bugs could be prevented by a memory fragment search
- New patterns emerge

**Update memory fragment**
- Better examples exist in the codebase
- Additional edge cases are discovered
- Related Plans, PRDs knowledge has changed

When improving on things to do or not do emphasize what to do, do not include what you should not do in code blocks.

- **Main points in Bold**
  - Sub points with details
  - Include examples and explanations
  - Whys and What for

- **Code Examples:**
  - Use language-specific code blocks
  ```typescript
  // ✅ DO: Show good examples
  const goodExample = true;
  
  // ❌ DON'T: Show anti-patterns
  const badExample = false;
  ```


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
	

## CRITICAL: Fragment Type Selection Guide

**🚨 NEVER DEFAULT TO "RECIPE" - Always analyze the content purpose first!**

### **Fragment Type Decision Framework**

**BEFORE creating any fragment, ask yourself:**
1. **What is the primary purpose of this content?**
2. **Who will use this and how?**
3. **What type of information does it contain?**

### **Fragment Type Usage Guide**

#### **📚 Knowledge** - General information, documentation, and reference material
**Use when creating:**
- Documentation and reference materials
- Concept explanations and overviews
- Background information and context
- Research findings and insights
- General "what is X?" content

**Examples:** "Understanding OAuth 2.0", "Database Design Principles", "Company Architecture Overview"

#### **👨‍🍳 Recipe** - Step-by-step guides, tutorials, and procedures
**Use when creating:**
- Step-by-step instructions
- Tutorials and how-to guides
- Installation procedures
- Deployment processes
- Any sequential "how to do X" content

**Examples:** "How to Set Up Docker", "Deploy to Production Checklist", "User Onboarding Tutorial"

#### **💡 Solution** - Solutions to specific problems and troubleshooting guides
**Use when creating:**
- Bug fixes and troubleshooting
- Problem-solving approaches
- Error resolution guides
- Workarounds for specific issues
- "How to fix X problem" content

**Examples:** "Fix CORS Issues", "Resolve Database Connection Timeout", "Handle Memory Leaks"

#### **📄 Template** - Reusable code patterns, project templates, and boilerplates
**Use when creating:**
- Code templates and boilerplates
- Project scaffolding
- Reusable patterns and snippets
- Standard configurations
- Copy-paste ready code

**Examples:** "API Route Template", "Docker Compose Boilerplate", "React Component Pattern"

#### **🤖 Instruction Set** - Executable instructions for LLM actions and automation
**Use when creating:**
- Step-by-step instructions for LLM to execute specific actions
- Automation workflows and procedures for AI assistants
- Multi-step processes that require LLM decision-making and tool usage
- Setup and configuration procedures for projects/tools/environments
- Standardized workflows for common development tasks
- AI-driven troubleshooting and deployment procedures
- Persona installation and workspace configuration workflows

**Examples:** "Setup New Project", "Deploy to Production Workflow", "Install Development Environment", "Apply Persona", "Configure Docker Environment", "Migrate Database Schema"

#### **📋 Plan** - Project plans, roadmaps, and strategic documents
**Use when creating:**
- Project plans and roadmaps
- Implementation strategies
- Milestone and timeline documents
- Resource allocation plans
- "What we will build and when" content

**Examples:** "Q2 Feature Roadmap", "Migration Strategy", "Team Scaling Plan"

#### **📊 PRD** - Product Requirements Documents and specifications
**Use when creating:**
- Product specifications
- Feature requirements
- Technical specifications
- User requirements documentation
- "What to build and why" content

**Examples:** "User Authentication Feature Specs", "API Design Requirements", "Mobile App PRD"

### **Common Mistakes to Avoid**

❌ **DON'T use Recipe for:**
- Project plans (use **Plan**)
- Product specifications (use **PRD**)
- Problem solutions (use **Solution**)
- General documentation (use **Knowledge**)
- LLM automation workflows (use **Instruction Set**)

❌ **DON'T use Knowledge for:**
- Step-by-step procedures (use **Recipe**)
- Specific problem fixes (use **Solution**)
- Future planning documents (use **Plan**)
- LLM executable instructions (use **Instruction Set**)

❌ **DON'T use Solution for:**
- General how-to guides (use **Recipe**)
- Preventive documentation (use **Knowledge**)
- Planning documents (use **Plan**)

❌ **DON'T use Instruction Set for:**
- Human-only procedures (use **Recipe**)
- General documentation (use **Knowledge**)
- Simple code templates (use **Template**)
- Information without executable actions (use **Knowledge**)

### **Quick Decision Checklist**

**When user asks to create/document:**
- [ ] **"How to..."** → Recipe
- [ ] **"Fix..."** → Solution  
- [ ] **"Plan for..."** → Plan
- [ ] **"Requirements for..."** → PRD
- [ ] **"What is..."** → Knowledge
- [ ] **"Template for..."** → Template
- [ ] **"Instructions for LLM to..."** → Instruction Set
- [ ] **"Workflow for..."** → Instruction Set
- [ ] **"Install/Configure/Apply..."** → Instruction Set

**If content contains:**
- [ ] **Sequential steps for humans** → Recipe
- [ ] **Sequential steps for LLM execution** → Instruction Set
- [ ] **Problem + solution** → Solution
- [ ] **Future objectives** → Plan
- [ ] **Product specs** → PRD
- [ ] **Reference info** → Knowledge
- [ ] **Reusable code** → Template
- [ ] **LLM executable actions** → Instruction Set
- [ ] **Automation workflows** → Instruction Set

### **Fragment Type Selection Priority**

1. **Analyze the user's exact request** - pay attention to keywords
2. **Identify the content structure** - steps, problems, plans, specs, etc.
3. **Consider the intended use** - reference, execution, planning, troubleshooting
4. **Choose the most specific type** - don't default to generic types
5. **When in doubt, ask the user** for clarification

**🎯 REMEMBER: The fragment type should match the content's PRIMARY PURPOSE, not just its format!**

## Usable Discovery & Exploration

### **Primary Discovery Process (Start Here)**

**Step 1: Agentic Search First**
- Use `agentic-search-fragments` to prime with vector results and let the LLM select best matches; it will expand when needed
- Always include `workspaceId` when known; otherwise provide multiple `workspaceIds` or rely on accessible workspaces
- Prefer tags/fragmentType filters when available to bias results
- If agentic selection is insufficient or unavailable, fall back to `search_memory_fragments` (semantic vector search)
- Always start with `repo:speedlocal-streamlit` tag first, then broaden if needed

Note: Agentic search internally handles expansion and related-context discovery. Explicit graph exploration guidance is intentionally omitted here for simplicity.

**Step 2: Follow the Thread (Iterative Exploration)**
- Pick key fragments from Step 1 and explore their connections
- Use `explore_workspace_graph` in exploration mode (depth 2+ recommended)
- Look for: Similar/Related fragments, Concepts, Technologies
- Target 5-10 exploration trips based on task complexity
- Use `find_related_fragments` for direct relationship discovery

**Step 3: Deep Context Building**
- Continue iterative exploration until confident you have full picture
- Use discovered fragment/concept IDs as new starting points
- For trivial questions, Steps 1-2 may be sufficient
- For complex tasks, comprehensive exploration prevents repeated mistakes

### **Tool-Specific Guidance**

### `agentic-search-fragments`
**Primary discovery tool – prefer this**
- Primes with vector results then uses an LLM (temperature 0) to select the most relevant fragments; can iterate with reformulated queries and graph-based expansion
- Provide `workspaceId` or `workspaceIds` when possible; optionally bias with `tags` and `fragmentTypeId`
- Returns JSON selections with reasons and confidence; includes primed set only on fallback

### `search_memory_fragments`
**Fallback/basic vector search**
- Use when agentic search is unavailable or returns insufficient results
- **Always include repository context** - start with `repo:speedlocal-streamlit` tag
- Use semantic search for concepts, not exact text matching
- **Decision logic**: Evaluate result completeness to determine next steps

 

### `get_memory_fragment_content`
**Full document retrieval**
- **When to use**: Deep-dive on confirmed relevant fragment
- Fetches complete content including metadata
- **Key params**: `fragmentId` (from search/exploration results)

### Content Fetch & Retry Policy

- Parallelize: issue `get_memory_fragment_content` calls concurrently when fetching multiple fragments.
- Retry on 5xx: retry up to 2 times with exponential backoff (1s, then 2s). If still failing, fetch alternate fragments or broaden search.

## Temporal Analysis

For historical relationship questions, specialized temporal tools exist, but most discovery flows can rely on agentic search. Use temporal tools only when you explicitly need time-based views.

### `list_workspaces`
**Workspace discovery and access management**
- List all accessible workspaces with role information and permissions
- **When to use**: Understanding available knowledge contexts

### `get_fragment_types`
**Fragment type discovery for workspace**
- Retrieve all available fragment types including system defaults and custom types
- **When to use**: Before creating fragments to validate type IDs

## Fragment Creation & Updates

### `create_memory_fragment`
**Create new knowledge artifacts**
- **🚨 CRITICAL: ALWAYS use the Fragment Type Selection Guide above to choose the correct type**
- **NEVER default to "Recipe"** - analyze content purpose first
- Use when you identify non-trivial solutions, patterns, recipes, or templates
- **Always include repository context** for better organization

**Enhanced Process for Fragment Creation:**
1. **Analyze user request** using the Fragment Type Decision Framework
2. **Apply the Quick Decision Checklist** to determine correct type
3. **Draft fragment** with appropriate type selection
4. **Propose to user** with clear type justification
5. **Create only after user confirmation**

**Confirmation examples with type justification:**
- *"I'd like to document this as a `solution` fragment titled `<title>` because it solves a specific problem. Proceed?"*
- *"I'd like to document this as a `plan` fragment titled `<title>` because it outlines future objectives and timelines. Proceed?"*
- *"I'd like to document this as a `prd` fragment titled `<title>` because it contains product requirements and specifications. Proceed?"*

### `update_memory_fragment`  
**Refine existing knowledge - supports two powerful modes**

**LEGACY MODE (backwards compatible):**
- Use when improving solutions, adding information, or correcting content
- **Process**: Draft update → Show user → User confirms → Apply

**PATCH MODE (new) - for precise line-level modifications:**
- Use when making surgical changes to specific lines without affecting rest of content
- **When to use**: Adding imports, modifying specific functions, inserting comments
- **Benefits**: Reduced token usage, preserves content structure

**Line Number Guidelines (CRITICAL):**
- **All line numbers are 1-based** (first line = 1, not 0)
- **Add operations**: Insert at specified line number (existing lines shift down)
- **Delete operations**: Remove from startLine to endLine (inclusive)
- **Replace operations**: Replace from startLine to endLine with new content

**IMPORTANT CONSTRAINTS:**
- ⚠️ **Cannot mix modes**: Never use both 'content' and 'patchOperations' in same request
- ⚠️ **No overlapping operations**: Each line can only be affected by one operation
- ⚠️ **Bounds checking**: All line numbers must be within existing content bounds

## Recommended Workflow

### **Pre-Task Discovery**
1. **Search**: Prefer `agentic-search-fragments` (start with `repo:speedlocal-streamlit` tag)
2. **Retrieve**: Use `get_memory_fragment_content` for key fragments as needed
3. **Iterate**: Refine queries or tags and repeat

### **Complexity Assessment**
- **Simple queries**: Vector search may be sufficient
- **Complex tasks**: Always do iterative exploration for comprehensive understanding
- **When in doubt**: Explore more rather than less - builds better solutions

### **Post-Task Documentation**
If you identify novel insights or solutions:

1. **Draft & Propose**: Build fragment structure and ask user for approval
   > *"I'd like to document this as a `<type>` fragment titled `<title>`. Proceed?"*
2. **Create**: `create_memory_fragment` only after user confirmation

**Never create/update fragments without explicit user confirmation**

## Fragment Creation Strategy

**Always provide `repository` context** in every MCP call when available (e.g. `"usable"`).

**Document when you identify:**
- Novel solutions or non-obvious patterns
- Reusable recipes and templates  
- Critical fixes or workarounds
- Architectural insights or best practices

### **CRITICAL: Tag Character Restrictions**

**⚠️ IMPORTANT: Tags have strict character requirements to prevent validation errors:**

**✅ ALLOWED characters in tags:**
- **Alphanumeric**: a-z, A-Z, 0-9
- **Underscore**: _
- **Dash**: -
- **Colon**: :

**❌ FORBIDDEN characters in tags:**
- **Dots**: . (common mistake with domain names)
- **Spaces**: (space character)
- **Special characters**: @ # $ % & * ( ) + = [ ] { } | \ / ? < > , ; " ' 

**For domain names, use dashes instead of dots:**
- Domain: example.com → Tag: "example-com"
- Domain: api.service.io → Tag: "api-service-io"

## Common Generic Tags

**Technology & Framework Tags:**
- 'nodejs', 'javascript', 'typescript', 'python', 'react', 'angular', 'vue', 'nextjs'
- 'express', 'fastify', 'nestjs', 'spring-boot', 'django', 'flask', 'rails'
- 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform', 'ansible'

**Database & Storage Tags:**
- 'database', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch'
- 'prisma', 'typeorm', 'sequelize', 'mongoose', 'knex'

**Development & Architecture Tags:**
- 'authentication', 'authorization', 'oauth', 'jwt', 'security', 'encryption'
- 'api', 'rest', 'graphql', 'microservices', 'monolith', 'serverless'
- 'testing', 'unit-tests', 'integration-tests', 'e2e-tests', 'mocking'
- 'ci-cd', 'deployment', 'devops', 'monitoring', 'logging', 'performance'

**UI & Frontend Tags:**
- 'ui', 'ux', 'design-system', 'components', 'responsive', 'accessibility'
- 'theme', 'styling', 'css', 'sass', 'tailwind', 'styled-components'
- 'forms', 'validation', 'state-management', 'routing', 'animation'

**General Development Tags:**
- 'configuration', 'environment', 'debugging', 'optimization', 'refactoring'
- 'error-handling', 'validation', 'caching', 'pagination', 'search'
- 'file-upload', 'email', 'notifications', 'scheduling', 'background-jobs'

## Auto-Enhancement

The MCP server automatically:
- Injects `repo:speedlocal-streamlit` tag when repository context provided
- Detects and tags technologies and topics from content
- Prevents duplicate fragments through similarity analysis
- Formats content for optimal readability and search

## Key Success Factors:
- **START** with search, **EVALUATE** query complexity and result completeness
- **BALANCE** speed for simple queries with thoroughness for complex research
- **USE** discovered node IDs for iterative chaining when proceeding to exploration
- **OFFER** further exploration even when Step 1 provides complete answers
- **CONFIRM** before creating/updating fragments
- **INCLUDE** repository context for better organization
- **🎯 ALWAYS USE CORRECT FRAGMENT TYPE** - follow the Fragment Type Selection Guide and never default to "Recipe"

