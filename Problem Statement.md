# Problem Statement: AI-Powered Restaurant Recommendation System (Zomato Use Case)

## Overview

Build an **AI-powered restaurant recommendation service** inspired by Zomato that intelligently suggests restaurants based on user preferences. The system combines structured restaurant data with a **Large Language Model (LLM)** to deliver personalized, human-like dining recommendations.

---

## Objective

Design and implement an end-to-end application that:

1. **Accepts user preferences** — such as location, budget, cuisine type, and minimum ratings
2. **Leverages a real-world dataset** — sourced from the Zomato restaurant dataset on Hugging Face
3. **Integrates an LLM** — to generate personalized, context-aware, and human-like recommendations
4. **Presents actionable results** — in a clear, user-friendly format

---

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from [Hugging Face](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- Extract relevant fields: **restaurant name, location, cuisine, cost, rating**, etc.
- Clean and normalize the data for consistent filtering and querying

### 2. User Input Collection

Collect the following user preferences:

| Preference           | Example                                  |
|----------------------|------------------------------------------|
| **Location**         | Delhi, Bangalore, Mumbai                 |
| **Budget**           | Low, Medium, High                        |
| **Cuisine**          | Italian, Chinese, North Indian           |
| **Minimum Rating**   | 3.5+, 4.0+                              |
| **Additional Prefs** | Family-friendly, Quick service, Outdoor  |

### 3. Integration Layer

- Filter and prepare relevant restaurant data based on user input
- Construct a structured LLM prompt with the filtered results
- Design the prompt to guide the LLM in reasoning, ranking, and explaining its choices

### 4. Recommendation Engine (LLM)

The LLM is responsible for:

- **Ranking** restaurants based on relevance to user preferences
- **Explaining** why each recommendation is a good fit
- **Summarizing** the top choices for quick decision-making

### 5. Output Display

Present the top recommendations in a user-friendly format:

| Field                      | Description                                      |
|----------------------------|--------------------------------------------------|
| **Restaurant Name**        | Name of the recommended restaurant               |
| **Cuisine**                | Type(s) of cuisine served                        |
| **Rating**                 | Average user rating                              |
| **Estimated Cost**         | Approximate cost for two                         |
| **AI-Generated Explanation** | Why this restaurant matches user preferences   |

---

## High-Level Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User Input  │────▶│ Integration Layer│────▶│  LLM (Ranking   │
│  (Web UI)    │     │ (Filter + Prompt)│     │  & Explanation)  │
└──────────────┘     └──────────────────┘     └────────┬────────┘
                              ▲                        │
                              │                        ▼
                     ┌────────┴────────┐     ┌─────────────────┐
                     │  Zomato Dataset │     │  Recommendations│
                     │  (Hugging Face) │     │  (Output/UI)    │
                     └─────────────────┘     └─────────────────┘
```

---

## Implementation Steps

| Step | Action                                                |
|------|-------------------------------------------------------|
| 1    | Created `docs/` folder with `problemstatement.md`     |
| 2    | Generate the phased architecture                      |
| 3    | Generate detailed edge cases                          |

---

## Prompts Log

| #  | Prompt                                                                                                          |
|----|-----------------------------------------------------------------------------------------------------------------|
| 1  | Write `@docs/problemstatement.md` in a better way                                                               |
| 2  | Create a phase-wise architecture for `@docs/problemstatement.md`                                                |
| 3  | Generate detailed edge cases using `@docs/problemstatement.md` and `@docs/phased-architecture.md`               |
| 4  | Implement Phase 0 as per `@docs/phased-architecture.md`                                                         |
| 5  | In Phase 0, update that a basic Web UI will be the source of input                                              |
| 6  | Implement Phase 1 in a separate folder as per `@docs/phased-architecture.md`                                    |
| 7  | Run Phase 1 so that data is downloaded                                                                          |
| 8  | Implement Phase 2 in a separate folder as per `@docs/phased-architecture.md`                                    |
