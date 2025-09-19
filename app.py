import os
import io
import json
import base64
from typing import List, Dict, Any

import gradio as gr
from dotenv import load_dotenv

from src.document_processor import DocumentProcessor
from src.gemini_analyzer import GeminiAnalyzer, GeminiUnavailable
from src.knowledge_graph import KnowledgeGraphGenerator
from src.compliance_monitor import ComplianceMonitor
from src.storage import Storage
from src.analyzer_router import AnalyzerRouter
from src.email_integration import EmailIntegration
from src.advanced_search import AdvancedSearch
from src.data_integration import UnifiedNamespaceSimulator, MaximoSimulator, SharePointSimulator

load_dotenv()

APP_TITLE = "DocSense AI - KMRL Intelligence Platform"

# Initialize core components
processor = DocumentProcessor()
kg = KnowledgeGraphGenerator()
compliance = ComplianceMonitor()
BASE_DIR = os.path.dirname(__file__)
storage = Storage(BASE_DIR)

# Initialize analyzer router
router = AnalyzerRouter("gemini")
LLM_READY = router.ready

# Initialize new components
email_integration = EmailIntegration()
advanced_search = AdvancedSearch()
uns_simulator = UnifiedNamespaceSimulator()
maximo_sim = MaximoSimulator()
sharepoint_sim = SharePointSimulator()

# Start real-time data simulation
uns_simulator.start_simulation()


def process_documents(files: List[gr.File], save_history: bool = False) -> Dict[str, Any]:
    results = []
    nodes = []
    edges = []

    for f in files or []:
        with open(f.name, 'rb') as fh:
            content = fh.read()
        meta = processor.extract_metadata(f.name, content)
        quick = processor.quick_skim(content, meta)

        llm = None
        if LLM_READY:
            llm = router.analyze(content, role=meta.get("suggested_role", "manager"))

        compliance_flags = compliance.check(meta, quick, llm)

        # Build knowledge graph nodes/edges
        n, e = kg.build_from_document(meta, quick, llm)
        nodes.extend(n)
        edges.extend(e)

        item: Dict[str, Any] = {
            "filename": os.path.basename(f.name),
            "metadata": meta,
            "quick_view": quick,
            "llm_analysis": llm,
            "compliance": compliance_flags,
        }

        # Optionally persist full analysis with dedup by file hash
        if save_history:
            fulltext = processor.extract_fulltext(content, meta.get("ext", ""))
            fhash = processor.file_hash(content)
            doc_id = storage.save_document(
                filename=f.name,
                file_hash=fhash,
                meta=meta,
                quick=quick,
                llm=llm,
                compliance=compliance_flags,
                fulltext=fulltext,
            )
            item["doc_id"] = doc_id

            # Index for advanced search
            advanced_search.index_document(str(doc_id), f.name, fulltext, meta)

            # Send notification email if configured
            if email_integration.email_ready:
                recipients = ["user@example.com"]  # Configure recipients
                email_integration.route_document(item, recipients)

        results.append(item)

    graph_json = kg.to_plotly(nodes, edges)
    return {
        "results": results,
        "graph": graph_json
    }


def advanced_search_query(query: str, search_type: str = "hybrid", filters: str = "") -> List[Dict[str, Any]]:
    """Perform advanced search with different methods"""
    if search_type == "full_text":
        results = advanced_search.full_text_search(query)
    elif search_type == "semantic":
        results = advanced_search.semantic_search(query)
    else:  # hybrid
        results = advanced_search.hybrid_search(query)

    # Apply filters if provided
    if filters:
        try:
            filter_dict = json.loads(filters)
            results = advanced_search.filter_by_metadata(filter_dict, results)
        except:
            pass

    return results

def get_realtime_data() -> Dict[str, Any]:
    """Get current real-time data from UNS"""
    return {
        "assets": uns_simulator.get_all_assets(),
        "work_orders": maximo_sim.get_work_orders()
    }

def send_email_notification(to_email: str, subject: str, body: str):
    """Send custom email notification"""
    return email_integration.send_notification(to_email, subject, body)

def build_ui():
    with gr.Blocks(title=APP_TITLE, theme=gr.themes.Soft()) as demo:
        gr.Markdown(f"# {APP_TITLE}")
        gr.Markdown(
            """
            **KMRL Knowledge Engine Implementation**

            Upload mixed documents (PDF, DOCX, images). The app will:
            - Detect language and classify type (English/Malayalam/Bilingual)
            - Extract quick actionable lines with multilingual support
            - Optional LLM: role-based analysis (if GOOGLE_API_KEY is set)
            - Show Knowledge Graph and Compliance flags
            - Advanced search capabilities (full-text, semantic, hybrid)
            - Real-time data integration with UNS simulation
            - Email notifications and routing
            - Optional: Save to History and search across past analyses
            """
        )

        with gr.Row():
            file_in = gr.File(label="Upload documents", file_count="multiple")
        with gr.Row():
            save_toggle = gr.Checkbox(label="Save to History", value=True)
            run_btn = gr.Button("Analyze")
            llm_status = gr.Markdown(
                "✅ LLM available (Gemini 2.5 Flash)" if LLM_READY else "ℹ️ LLM not configured. Set GOOGLE_API_KEY for deeper analysis."
            )

        with gr.Tabs():
            with gr.TabItem("Results"):
                # Use Code to bypass JSON schema introspection bugs
                results_out = gr.Code(label="Per-document Analysis", language="json")
            with gr.TabItem("Knowledge Graph"):
                graph_out = gr.Plot(label="Entities & Relationships")
            with gr.TabItem("Advanced Search"):
                with gr.Row():
                    search_query_adv = gr.Textbox(label="Search Query", placeholder="Enter search terms...")
                    search_type = gr.Dropdown(["hybrid", "full_text", "semantic"], value="hybrid", label="Search Type")
                    search_filters = gr.Textbox(label="Metadata Filters (JSON)", placeholder='{"doc_type": "Safety"}')
                with gr.Row():
                    search_btn_adv = gr.Button("Advanced Search")
                search_out_adv = gr.JSON(label="Advanced Search Results")
            with gr.TabItem("Real-Time Data Integration"):
                with gr.Row():
                    refresh_btn = gr.Button("Refresh Data")
                realtime_out = gr.JSON(label="UNS & Maximo Data")
            with gr.TabItem("Email Integration"):
                with gr.Row():
                    email_to = gr.Textbox(label="To Email", placeholder="recipient@example.com")
                    email_subject = gr.Textbox(label="Subject", placeholder="Document Processed")
                    email_body = gr.Textbox(label="Body", lines=3, placeholder="Custom email body...")
                with gr.Row():
                    send_email_btn = gr.Button("Send Notification")
                email_status = gr.JSON(label="Email Status")
            with gr.TabItem("History / Basic Search"):
                with gr.Row():
                    search_query = gr.Textbox(label="Search (FTS)", placeholder="e.g., CMRS OR incident OR vendor")
                with gr.Row():
                    search_btn = gr.Button("Search")
                    recent_btn = gr.Button("Load Recent")
                with gr.Row():
                    search_out = gr.JSON(label="Search Results")
                    recent_out = gr.JSON(label="Recent Analyses")

        def _run(files, save_history):
            data = process_documents(files, save_history=bool(save_history))
            # Pretty-print JSON for Code component
            return json.dumps(data["results"], ensure_ascii=False, indent=2), data["graph"]

        def _search(q):
            return storage.search(q)

        def _recent():
            return storage.recent()

        run_btn.click(_run, inputs=[file_in, save_toggle], outputs=[results_out, graph_out])
        search_btn.click(_search, inputs=[search_query], outputs=[search_out])
        recent_btn.click(_recent, outputs=[recent_out])

        # Advanced search
        search_btn_adv.click(advanced_search_query, inputs=[search_query_adv, search_type, search_filters], outputs=[search_out_adv])

        # Real-time data
        refresh_btn.click(get_realtime_data, outputs=[realtime_out])

        # Email
        send_email_btn.click(send_email_notification, inputs=[email_to, email_subject, email_body], outputs=[email_status])

    return demo


if __name__ == "__main__":
    ui = build_ui()
    # Try different ports if 8501 is busy
    ports_to_try = [8501, 7860, 8502, 8503]
    for port in ports_to_try:
        try:
            print(f"Trying to launch on port {port}...")
            ui.launch(server_name="0.0.0.0", server_port=port)
            break
        except OSError as e:
            print(f"Port {port} is busy, trying next port...")
            if port == ports_to_try[-1]:
                print("All ports are busy. Please close other applications or specify a different port.")
                print("You can also set GRADIO_SERVER_PORT environment variable to a specific port.")
                raise e