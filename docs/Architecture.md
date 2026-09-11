# 🏗 Core Architecture

OmniAgent relies on the `crewai` and `langchain` frameworks to orchestrate its autonomous agents. 

## The Semantic Router
OmniAgent implements an incredibly fast **Semantic Router**.
1. **Lexical Fast-Path**: The router scans user input for predefined keywords (e.g. `firewall`, `port`, `refactor`). If a match is found, it bypasses LLM execution to save time.
2. **Semantic Fallback**: If the prompt is ambiguous, OmniAgent passes the query to a local LLM to classify the user's intent into predefined domains (`PLAN`, `ARCHITECT`, `CODE`, `TEST`, etc.).

## The Universal Oracle
OmniAgent operates primarily via **Ollama** running locally on the host machine to ensure strict data privacy. However, local models can occasionally hallucinate or lack external knowledge.

To solve this, OmniAgent features a `Universal Oracle`. During the onboarding wizard, the system detects your installed CLI AI tools (like `gemini`, `claude`, or `chatgpt`) and exposes them as a fallback tool. If the local agents get stuck, they query the Oracle.
