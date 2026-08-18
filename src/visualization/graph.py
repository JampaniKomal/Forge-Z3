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
        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", directed=True)

        # Build node vulnerability lookup
        vuln_map = {}
        for v in topology.vulnerabilities:
            if v.node_id not in vuln_map:
                vuln_map[v.node_id] = []
            vuln_map[v.node_id].append(v.cve_id)

        # Add Nodes
        for node in topology.nodes:
            title = f"Node {node.node_id}: {node.name}"
            if node.node_id in vuln_map:
                title += f"\nVulnerabilities: {', '.join(vuln_map[node.node_id])}"

            # Styling: Attacker is Red and large, Targets are Blue
            color = "#ff4b4b" if node.node_id == 0 else "#4b8bff"
            size = 30 if node.node_id == 0 else 20

            net.add_node(
                node.node_id,
                label=node.name,
                title=title,
                color=color,
                size=size
            )

        # Add Edges
        for edge in topology.edges:
            net.add_edge(
                edge.source_id,
                edge.target_id,
                title=f"Port: {edge.port}",
                label=str(edge.port),
                color="#aaaaaa"
            )

        # Configure physics for a beautiful spread-out layout
        net.barnes_hut(spring_length=200, spring_strength=0.05)

        output_path = os.path.join(self.build_dir, filename)
        net.write_html(output_path)
        return output_path
