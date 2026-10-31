"""Verify navigation-loop termination with real Chrome and the production LangGraph."""
# Resolve repository modules for direct execution.
import sys
# Locate controlled public fixtures independently of the launch directory.
from pathlib import Path
# Serve only deterministic local pages.
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
# Keep the process-wide working directory unchanged.
from functools import partial
# Run the fixture service beside the real graph.
from threading import Thread
# Enable direct repository imports.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
# Construct genuine executor and controller dependencies.
from services.run_controller import create_browser_adapter, execute_run
# Supply the same validated settings as the UI.
from config.settings import RunConfiguration
# Retain actual status and cancellation behavior.
from services.monitoring import RunMonitor
# Emit only ordinary allowed browser actions.
from domain.models import AgentDecision

# Deliberately reproduce the observed bounce without a paid model request.
class BouncingProvider:
    """Alternate actual chapter URLs while producing no source evidence."""
    # Retain the exact local origin and count actual decisions.
    def __init__(self,origin):
        """Bind one controlled website for this explicit diagnostic."""
        # Do not authorize or contact unrelated hosts.
        self.origin=origin
        # Count model-shaped decisions independently of browser effects.
        self.calls=0
    # Produce one ordinary action from the current actual observation.
    def decide(self,task,observation,history):
        """Navigate to the opposite chapter, recreating the failing bounce."""
        # Track actual graph requests.
        self.calls+=1
        # Choose the other real fixture page.
        path="chapter_b.html" if observation.url.endswith("chapter_a.html") else "chapter_a.html"
        # Ordinary native navigation must not evade progress verification.
        return AgentDecision(kind="navigate",target=self.origin+path)

# Keep all resources owned by this explicit practical diagnostic.
def main():
    """Require an honest partial outcome after repeated real navigations."""
    # Serve controlled pages without external credentials.
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(Path(__file__).parent/"fixtures")))
    # Keep the private server available throughout the graph run.
    Thread(target=server.serve_forever,daemon=True).start()
    # Use the same hostname boundary for every actual navigation.
    origin=f"http://127.0.0.1:{server.server_port}/"
    # Keep only the model collaborator deterministic.
    provider=BouncingProvider(origin)
    # Use the real selected MCP executor.
    adapter=create_browser_adapter("playwright_mcp")
    # Execute the production controller, graph, browser, verification, and cleanup.
    try:
        # The fake key belongs only to this injected-provider diagnostic.
        result=execute_run("Retrieve both chapters",origin+"chapter_a.html",RunConfiguration("gemini","playwright_mcp",False,"nonsecret-test-marker"),adapter,provider,RunMonitor())
        # A navigation cycle must terminate without claiming task success.
        assert result["finished"] and not result["verified"],result
        # Require the specific evidence-progress guard to explain termination.
        assert "Repeated navigation" in result["blocker"],result
        # Termination must follow actual repeated arrivals, not a global time cap.
        assert 5 <= provider.calls <= 6,provider.calls
        # Report only safe practical proof and source-artifact references.
        print({"real_browser":True,"navigation_calls":provider.calls,"status":result["status"],"verified":result["verified"]})
    # The production controller owns browser closure; this block releases only the fixture.
    finally:
        # Stop the owned local HTTP thread.
        server.shutdown()
        # Release its private socket.
        server.server_close()

# Importing this diagnostic must not start browser or server processes.
if __name__ == "__main__":
    # Run only from this explicit practical test command.
    main()
