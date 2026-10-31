"""Durable source evidence and deterministic TXT/Markdown result assembly.

This service owns captured UI blocks, source relationships, ordering, and coverage.
It never asks an LLM to rewrite extracted content. SQLite stores every captured
block outside navigation prompt limits and survives pause or interrupted execution.
"""
# Preserve exact block metadata in a portable manifest.
import json
# Build capture identities without collapsing legitimate repeated values.
import hashlib
# Retain complete evidence without keeping every page in the model context.
import sqlite3
# Resolve immutable run artifacts.
from pathlib import Path
# Escape literal source punctuation when creating a structural Markdown view.
import re
# Normalize tracking URLs and stable entity destinations before deduplication.
from services.identity import canonical_url, entity_identity
# Select exact task-relevant records without asking a model to rewrite them.
from agent.goals import goal_records


# Store complete evidence for one run in an isolated artifact directory.
class EvidenceStore:
    """Persist exact blocks and page coverage, then assemble outputs from those records."""

    # Initialize the local store without provider credentials or browser objects.
    def __init__(self, directory):
        """Create/open one run-owned evidence database and its artifact directory."""
        # Normalize artifact paths before any exports are written.
        self.directory = Path(directory).resolve()
        # Create only this run's directory.
        self.directory.mkdir(parents=True, exist_ok=True)
        # Keep SQLite on the worker thread that owns extraction.
        self.connection = sqlite3.connect(self.directory / "evidence.sqlite3")
        # Persist complete metadata, including code whitespace and table relationships.
        self.connection.execute("CREATE TABLE IF NOT EXISTS blocks (capture_key TEXT PRIMARY KEY, page_no INTEGER, region_no INTEGER, y REAL, x REAL, sequence INTEGER, payload TEXT)")
        # Add state ordering to older run databases without losing existing evidence.
        columns = {row[1] for row in self.connection.execute("PRAGMA table_info(blocks)")}
        # A state sequence keeps tab and pagination versions from interleaving by vertical position.
        if "state_no" not in columns:
            # Existing captures belong to their initial interface state.
            self.connection.execute("ALTER TABLE blocks ADD COLUMN state_no INTEGER DEFAULT 0")
        # Retain per-page state discovery order during this owned run.
        self._states = {}
        # Keep page coverage separate from text fidelity.
        self.connection.execute("CREATE TABLE IF NOT EXISTS pages (url TEXT PRIMARY KEY, sequence INTEGER, payload TEXT)")
        # Retain initial schema creation durably.
        self.connection.commit()

    # Preserve a viewport capture before moving or recycling DOM rows.
    def add(self, capture, scope, page_no, region_no):
        """Insert new exact source blocks; repeated captures of the same record are idempotent."""
        # Bind each block to the actual page that supplied it.
        url = capture["url"]
        # Use one comparison identity across tracking, fragment, and sibling-subdomain variants.
        page_identity = canonical_url(url)
        # Record each selected-tab/pagination state once in its real encounter order.
        state_key = json.dumps(capture.get("view_state", []), ensure_ascii=False)
        # Each source page owns an independent ordered state ledger.
        states = self._states.setdefault(url, [])
        # Discover real replacement states without using model-generated descriptions.
        if state_key not in states:
            # Preserve captured state order rather than alphabetizing labels.
            states.append(state_key)
        # All blocks from this capture belong to the same actual UI state.
        state_no = states.index(state_key)
        # Read the next stable sequence once per viewport instead of counting every inserted block.
        sequence = self.connection.execute("SELECT COALESCE(MAX(sequence),-1)+1 FROM blocks").fetchone()[0]
        # Preserve source order and UI relationships for every nonempty block.
        for block in capture.get("blocks", []):
            # Never strip source whitespace or reconstruct text from a model answer.
            text = block.get("text", "")
            # Ignore empty layout blocks without changing nonempty source content.
            if not text:
                # Continue to the next actual source block.
                continue
            # Canonical entity URLs survive document reloads and tracking-query changes.
            entity_key = entity_identity(block.get("entity_url", ""), block.get("entity_key", ""))
            # Structural paths survive viewport overlap while legacy keys preserve existing tests.
            structural_key = block.get("stable_path") or block["key"]
            # Whole record containers use their logical entity instead of a changing list position.
            record_container = block.get("kind") in {"li", "table_row", "article", "record"} and bool(entity_key)
            # Fixed/sticky chrome and logical records survive scrolling, reloads, and list reordering.
            source_key = ["persistent", block.get("kind"), text, structural_key] if block.get("persistent") else (["entity", entity_key, block.get("kind")] if record_container else [entity_key, structural_key, block.get("kind")])
            # Stable semantic identity distinguishes equal values in different real records.
            identity = [page_identity, scope, capture.get("view_state", []), source_key, text]
            # Hash only identity data; source contents remain intact in the payload.
            key = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()
            # Preserve explicit provenance separately from the raw block text.
            payload = {**block, "url": url, "canonical_url": page_identity, "entity_key": entity_key or block.get("entity_key", ""), "scope": scope, "region": region_no, "view_state": capture.get("view_state", []), "ui_state": [{"id": item["id_label"], "label": item.get("text", "")} for item in capture.get("elements", []) if item.get("selected") == "true"]}
            # Ignore only repeated captures of the same source record and exact version.
            self.connection.execute("INSERT OR IGNORE INTO blocks (capture_key,page_no,region_no,y,x,sequence,payload,state_no) VALUES (?,?,?,?,?,?,?,?)", (key, page_no, region_no, block.get("y", 0), block.get("x", 0), sequence, json.dumps(payload, ensure_ascii=False), state_no))
            # Reserve a stable tie-breaker without another table count.
            sequence += 1
        # Commit before scrolling can discard virtualized source nodes.
        self.connection.commit()

    # Record a page's actual completion evidence and known limitations.
    def page(self, url, report, page_no):
        """Persist typed traversal results independently of model finish proposals."""
        # Save a serializable coverage manifest with its actual page order.
        self.connection.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?)", (url, page_no, json.dumps(report, ensure_ascii=False)))
        # Keep partial/complete coverage available after interruption.
        self.connection.commit()

    # Read blocks in deterministic page, region, and rendered-source order.
    def blocks(self):
        """Return complete source metadata without any model-context truncation."""
        # Order by measured source position; sequence resolves identical coordinates.
        rows = self.connection.execute("SELECT payload FROM blocks ORDER BY page_no,state_no,region_no,y,x,sequence").fetchall()
        # Decode metadata without modifying any captured source text.
        return [json.loads(row[0]) for row in rows]

    # Expose coverage for final verification and the results UI.
    def pages(self):
        """Return each visited page's capture report in traversal order."""
        # Preserve actual page order rather than alphabetically sorting URLs.
        rows = self.connection.execute("SELECT url,payload FROM pages ORDER BY sequence").fetchall()
        # Keep source URLs separate from verbatim output text.
        return [{"url": url, **json.loads(payload)} for url, payload in rows]

    # Assemble the exact-text view without generated summaries or imposed JSON conversion.
    def selected_blocks(self, goal=None):
        """Return complete evidence or the exact finite record subset requested by the goal."""
        # Read all durable blocks once in deterministic source order.
        blocks = self.blocks()
        # Ordinary page/site tasks retain the complete faithfully captured source.
        if not goal or goal.get("mode") != "collect_entities":
            # Do not impose a record schema on broad information requests.
            return blocks
        # Select unique qualifying records through generalized constraint rules.
        records = goal_records(blocks, goal)
        # Respect an explicit count without shortening any selected record's wording.
        limit = goal.get("required_count")
        # Return the first requested number in real rendered source order.
        return records[:int(limit)] if limit else records

    # Assemble the exact-text view without generated summaries or imposed JSON conversion.
    def text(self, goal=None):
        """Join task-relevant original block strings, retaining internal whitespace."""
        # Add separators only between distinct UI blocks; never trim the blocks themselves.
        return "\n\n".join(block["text"] for block in self.selected_blocks(goal))

    # Assemble a structural Markdown companion while retaining exact-text as authoritative.
    def markdown(self, goal=None):
        """Preserve heading/code/table relationships without interpreting source as executable HTML."""
        # Accumulate deterministic presentation fragments.
        output = []
        # Track the current table to emit its header once.
        table = None
        # Read all source blocks in their captured order.
        for block in self.selected_blocks(goal):
            # Keep the original text as the only content source.
            text = block["text"]
            # Preserve preformatted content inside an appropriately long fence.
            if block["kind"] == "code":
                # Avoid closing a code block when its source contains backticks.
                fence = "`" * max(3, max((len(match.group()) for match in re.finditer(r"`+", text)), default=0) + 1)
                # Keep indentation and line breaks inside the fence unchanged.
                output.append(fence + "\n" + text + "\n" + fence)
            # Retain table cell associations rather than splitting on arbitrary whitespace.
            elif block["kind"] == "table_row":
                # Escape Markdown control characters only in the presentation companion.
                cells = [cell["text"].replace("|", "\\|").replace("\n", "<br>") for cell in block["cells"]]
                # Add a row with all its original labels and values.
                output.append("| " + " | ".join(cells) + " |")
                # Introduce a table header on the first captured row.
                if table != block["table"]:
                    # Markdown requires a separator row; exact multiline cells remain in TXT/manifest.
                    output.append("| " + " | ".join("---" for cell in cells) + " |")
                    # Retain the active table identity.
                    table = block["table"]
            # Represent headings with their original hierarchy and wording.
            elif block["kind"] == "heading":
                # Escape literal source punctuation while adding only structural heading markers.
                output.append("#" * block.get("level", 1) + " " + re.sub(r"([\\`*_{}\[\]<>])", r"\\\1", text))
            # Preserve prose without allowing source HTML or Markdown to execute formatting unexpectedly.
            else:
                # Escaping changes only the Markdown encoding, not visible original wording.
                output.append(re.sub(r"([\\`*_{}\[\]<>])", r"\\\1", text))
        # Keep exact TXT/manifest alongside this explicitly structural presentation.
        return re.sub(r"(?m)(^\|[^\n]*\|)\n\n(?=\|)", r"\1\n", "\n\n".join(output))

    # Publish complete artifacts for both success and partial results.
    def export(self, goal=None):
        """Write TXT, Markdown, and provenance JSON, returning their absolute paths."""
        # Keep generated files within the run-owned directory.
        paths = {name: self.directory / filename for name, filename in (("text", "result.txt"), ("markdown", "result.md"), ("manifest", "manifest.json"))}
        # Export complete source text independently from model token/output limits.
        paths["text"].write_text(self.text(goal), encoding="utf-8")
        # Export the deterministic structural companion.
        paths["markdown"].write_text(self.markdown(goal), encoding="utf-8")
        # Preserve exact cells, relationships, and limitations in a separately inspectable manifest.
        paths["manifest"].write_text(json.dumps({"pages": self.pages(), "blocks": self.blocks(), "selected_blocks": self.selected_blocks(goal)}, indent=2, ensure_ascii=False), encoding="utf-8")
        # Return usable absolute filesystem paths rather than embedding large files in events.
        return {name: str(path) for name, path in paths.items()}

    # Release the worker-owned database connection explicitly.
    def close(self):
        """Close SQLite after final export; already written artifacts remain readable."""
        # Ensure all pending source evidence is durably stored.
        self.connection.commit()
        # Release only this run's database resources.
        self.connection.close()
