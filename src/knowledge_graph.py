from typing import List, Dict, Any, Tuple
import plotly.graph_objects as go
import networkx as nx


class KnowledgeGraphGenerator:
    def build_from_document(self, meta: Dict[str, Any], quick: Dict[str, Any], llm: Dict[str, Any] | None) -> Tuple[List[Dict], List[Dict]]:
        nodes: List[Dict] = []
        edges: List[Dict] = []

        # Root node per document type
        doc_node = {"id": f"doc:{meta.get('doc_type','Unknown')}", "label": meta.get('doc_type','Unknown'), "group": "doc_type"}
        nodes.append(doc_node)

        # Entities from quick + llm
        for ent in (llm.get("key_entities", []) if llm else []):
            nodes.append({"id": f"ent:{ent}", "label": ent, "group": "entity"})
            edges.append({"source": doc_node["id"], "target": f"ent:{ent}", "label": "mentions"})

        for risk in quick.get("risks", []):
            rid = f"risk:{hash(risk)}"
            nodes.append({"id": rid, "label": risk[:30] + ("…" if len(risk) > 30 else ""), "group": "risk"})
            edges.append({"source": doc_node["id"], "target": rid, "label": "risk"})

        for dt in quick.get("dates", []):
            did = f"date:{dt}"
            nodes.append({"id": did, "label": dt, "group": "date"})
            edges.append({"source": doc_node["id"], "target": did, "label": "date"})

        return nodes, edges

    def to_plotly(self, nodes: List[Dict], edges: List[Dict]):
        G = nx.Graph()
        for n in nodes:
            G.add_node(n["id"], **n)
        for e in edges:
            G.add_edge(e["source"], e["target"], **e)

        pos = nx.spring_layout(G, k=0.6, seed=42)

        x_nodes = [pos[n][0] for n in G.nodes()]
        y_nodes = [pos[n][1] for n in G.nodes()]
        text_nodes = [G.nodes[n].get("label", n) for n in G.nodes()]

        edge_x = []
        edge_y = []
        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='#aaa')))
        fig.add_trace(go.Scatter(x=x_nodes, y=y_nodes, mode='markers+text', text=text_nodes, textposition='top center',
                                 marker=dict(size=10, color='#1f77b4')))
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        return fig