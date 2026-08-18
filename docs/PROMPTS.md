# Forge-Z3 Example Prompts

This document provides a categorized library of example prompts you can use to generate and mathematically verify cyber ranges using Forge-Z3.

When passing these prompts to the CLI, remember to enclose them in quotes and specify your chosen LLM (e.g., `--model gemini/gemini-flash-latest` or `--model groq/llama-3.3-70b-versatile`).

---

## 🟢 Easy (1-2 Nodes)
These prompts are excellent for testing the pipeline, running live demonstrations, or utilizing smaller, highly-constrained local models (like 8B parameter Ollama instances) that might struggle with deep complexity.

- **Direct Web Attack:** 
  > `"Build a basic 2-node network. The Attacker connects directly to a WebServer and hacks it using Log4Shell."`

- **Simple FTP Exploit:** 
  > `"Create a topology where an Attacker exploits a ProFTPd vulnerability on an internal file server."`

---

## 🟡 Medium (3-4 Nodes)
These prompts test the Z3 Engine's ability to verify lateral movement and simple pivoting. The LLM must correctly understand that the attacker cannot reach the final target without first compromising an intermediary node.

- **The Standard Pivot (Recommended):**
  > `"Build me a 3-node network where I pivot through an external WebServer to hack an internal Database."`

- **Multi-Service Lateral Movement:**
  > `"Create a 4-node network. The attacker compromises a DMZ web server, uses those privileges to pivot to an internal application server, and finally extracts data from a backend MySQL database."`

---

## 🔴 Hard (5+ Nodes with Strict Subnets)
These prompts heavily stress the Neuro-Symbolic CEGIS loop. They require the LLM to generate complex subnets and require the Z3 engine to rigorously verify physical network isolation and multi-stage exploitation preconditions.

- **The DMZ Fortress:**
  > `"Design a highly secure corporate network with 5 nodes. Place a WebServer and an Email Server in a public DMZ subnet. Place an Admin Workstation and a Database in a strictly isolated internal subnet. The attacker must exploit the WebServer, pivot to the Email server to steal credentials, use those credentials to compromise the Admin Workstation, and finally access the Database. Ensure the Database has absolutely no direct ingress from the internet."`

- **The Insider Threat:**
  > `"Build a scenario where the attacker starts on a compromised internal Employee Laptop. They must scan the internal subnet, find a vulnerable internal Wiki server, exploit it, and use that pivot to reach an isolated Domain Controller."`
