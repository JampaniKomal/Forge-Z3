"""
Cyber Range Visualization Engine using PyVis.
Generates interactive 3D HTML graphs of the generated topologies.
"""

import os

from pyvis.network import Network

from src.z3_engine.schema import Topology


class TopologyVisualizer:
    def __init__(self, build_dir: str = "build"):
        self.build_dir = build_dir
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)

    def generate_html(self, topology: Topology, filename: str = "topology.html"):
        """Generates an interactive HTML network graph."""
        net = Network(height="800px", width="100%", bgcolor="#050510", font_color="#e0e0e0", directed=True)

        # Build node vulnerability lookup
        vuln_map = {}
        for v in topology.vulnerabilities:
            if v.node_id not in vuln_map:
                vuln_map[v.node_id] = []
            vuln_map[v.node_id].append(v.cve_id)

        # Add Nodes
        for node in topology.nodes:
            title = f"Node {node.node_id}: {node.name}"
            label_text = node.name

            if node.node_id in vuln_map:
                cves = ', '.join(vuln_map[node.node_id])
                title += f"\nVulnerabilities: {cves}"
                label_text += f"\n🚨 {cves}" # Show CVE directly on the graph!

            # Styling: Cyberpunk Aesthetics
            if node.node_id == 0:
                # Attacker Node (Neon Red)
                node_color = {"background": "#ff003c", "border": "#8a0020", "highlight": {"background": "#ff3366", "border": "#ffffff"}}
                shadow = {"enabled": True, "color": "#ff003c", "size": 25, "x": 0, "y": 0}
                shape = "dot"
                size = 35
            else:
                # Target Node (Neon Cyan)
                node_color = {"background": "#00f0ff", "border": "#008a93", "highlight": {"background": "#33f3ff", "border": "#ffffff"}}
                shadow = {"enabled": True, "color": "#00f0ff", "size": 20, "x": 0, "y": 0}
                shape = "hexagon" if node.node_id in vuln_map else "dot"
                size = 25

            net.add_node(
                node.node_id,
                label=label_text,
                title=title,
                color=node_color,
                size=size,
                shape=shape,
                shadow=shadow,
                font={"color": "#ffffff", "face": "Courier New", "size": 16, "bold": True}
            )

        # Add Edges
        for edge in topology.edges:
            net.add_edge(
                edge.source_id,
                edge.target_id,
                title=f"Port: {edge.port}",
                label=f" Port: {edge.port} ",
                color={"color": "#4b5563", "highlight": "#00ffcc"},
                width=3,
                font={"color": "#a1a1aa", "face": "Courier New", "size": 12, "background": "#050510"}
            )

        # Configure physics for a beautiful spread-out layout
        net.set_options("""
        var options = {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -4000,
              "centralGravity": 0.3,
              "springLength": 250,
              "springConstant": 0.04,
              "damping": 0.09
            },
            "minVelocity": 0.75
          }
        }
        """)

        output_path = os.path.join(self.build_dir, filename)
        net.write_html(output_path)
        return output_path
