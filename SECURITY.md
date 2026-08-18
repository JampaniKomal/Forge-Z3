# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | ✅        |

## Reporting a Vulnerability

If you discover a security vulnerability in Forge-Z3, please report it responsibly:

1. **Do NOT open a public GitHub issue.**
2. Email the maintainer directly at: [jampanikomal@gmail.com] (replace with your actual email).
3. Include a detailed description of the vulnerability, steps to reproduce, and potential impact.
4. You will receive an acknowledgment within 48 hours.

## Security Considerations

Forge-Z3 generates Infrastructure-as-Code (IaC) configurations that deploy intentionally vulnerable virtual machines. 

### ⚠️ Important Warnings

- **Never deploy generated configurations on production networks.** Generated environments contain real, exploitable CVEs (e.g., Log4Shell, EternalBlue).
- **Always run generated ranges in isolated, air-gapped environments** (e.g., host-only VirtualBox networks, isolated Docker bridge networks).
- **Do not expose generated VMs to the internet.** They are designed to be vulnerable.
- **API keys:** If using an external LLM API (Gemini, Groq), store your API key in a `.env` file. Never commit `.env` to version control. The `.gitignore` already excludes it.

## Secure Coding Practices

This project follows these secure coding standards:

1. **Input Validation:** All LLM outputs are validated against strict Pydantic schemas before processing. No raw string parsing.
2. **No `eval()` or `exec()`:** Datalog predicates are constructed via safe string formatting, never dynamic code execution.
3. **Subprocess Safety:** All `subprocess` calls use explicit argument lists (not `shell=True`) to prevent command injection.
4. **Dependency Scanning:** We use `bandit` for static security analysis and `safety` for dependency vulnerability scanning.
5. **Principle of Least Privilege:** Generated IaC configurations use isolated network segments by default.
