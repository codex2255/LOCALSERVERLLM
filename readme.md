# Local LLM API Gateway

A lightweight, 1-page Python application that transforms any local machine (like an old ThinkPad, Mac, or desktop) into a secure, headless, OpenAI-compatible AI server. 

It acts as a bouncer and router for [Ollama](https://ollama.com/), securing your local models with dynamic API key authentication while serving a sleek Web Dashboard so you can monitor and interact with the node from anywhere on your network.

## Features
* **OpenAI Drop-In Replacement:** Point any client (like Chatbox, LangChain, or Autogen) to this server instead of OpenAI.
* **Model Agnostic:** Automatically supports and routes requests to ANY open-source model you pull via Ollama (Llama 3, Mistral, Gemma, etc.).
* **Dynamic Key Management:** Generate and revoke API keys instantly via the web GUI.
* **Built-in Dashboard:** A single-page Web GUI providing server status, API keys, and dynamically listed installed models.
* **Streaming Support:** Fully supports token streaming out of the box.

## Quickstart

### 1. Install Ollama (The AI Engine)
This gateway routes traffic to Ollama, so it must be installed on the host machine first.
* **Linux/macOS:** `curl -fsSL https://ollama.com/install.sh | sh`
* **Windows:** Download from [ollama.com/download](https://ollama.com/download)

Open a terminal and pull your first model (e.g., Llama 3.1 8B):
```bash
ollama pull llama3.1