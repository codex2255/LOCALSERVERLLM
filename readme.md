# Local LLM API Gateway

A lightweight, 1-page Python application that transforms any local machine (like an old ThinkPad) into a secure, headless, OpenAI-compatible AI server. 

It acts as a bouncer and router for [Ollama](https://ollama.com/), securing your local models with API key authentication while serving a sleek Web Dashboard so you can monitor and interact with the node from anywhere on your network.

## Features
* **OpenAI Drop-In Replacement:** Point any client (like Chatbox, LangChain, or Autogen) to this server instead of OpenAI.
* **Model Agnostic:** Automatically supports and routes requests to ANY open-source model you pull via Ollama (Llama 3, Mistral, Gemma, etc.).
* **Built-in Dashboard:** A single-page Web GUI providing server status, active API keys, and dynamically listed installed models.
* **Streaming Support:** Fully supports token streaming out of the box.

## Requirements
* Python 3.8+
* [Ollama](https://ollama.com/) installed and running on the host machine.

