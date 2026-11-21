import json
from mcp.server.fastmcp import FastMCP
import ollama

mcp = FastMCP("Ollama Local Assistant")

@mcp.tool()
def list_ollama_models() -> str:
    """List models installed in local Ollama (e.g. llama3.2, qwen)."""
    try:
        models = ollama.list()
        names = [m.model for m in models.models]
        return json.dumps({"status": "success", "models": names})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
def ask_ollama(prompt: str, model: str = "llama3.2") -> str:
    """
    Send a coding, reasoning, analysis, or conversational prompt to local Ollama (default: llama3.2).
    Runs completely free, locally and privately on your machine.
    """
    try:
        # Strip :latest if present to match ollama standard tags
        clean_model = model.replace(":latest", "")
        response = ollama.chat(
            model=clean_model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.4}
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error connecting to local Ollama: {e}"

if __name__ == "__main__":
    mcp.run()
