"""
IaC Compiler: Translates Z3-Verified Topologies into Vagrant and Ansible code.
"""

import os

from src.knowledge_base.physics import get_cve_map
from src.z3_engine.schema import Topology


class IaCCompiler:
    def __init__(self, build_dir: str = "build"):
        self.build_dir = build_dir
        self.cve_map = get_cve_map()

        # Ensure build directory exists
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)

    def compile(self, topology: Topology):
        """Generates all necessary IaC files."""
        self._generate_vagrantfile(topology)
        self._generate_ansible_inventory(topology)
        self._generate_ansible_playbook(topology)

    def _generate_vagrantfile(self, topology: Topology):
        """Generates a multi-machine Vagrantfile using ubuntu/focal64."""
        lines = [
            "# -*- mode: ruby -*-",
            "# vi: set ft=ruby :",
            "Vagrant.configure('2') do |config|",
            "  config.vm.box = 'ubuntu/focal64'",
            "  # Shared Ansible Provisioning",
            "  config.vm.provision 'ansible' do |ansible|",
            "    ansible.playbook = 'site.yml'",
            "    ansible.inventory_path = 'inventory.ini'",
            "  end"
        ]

        for node in topology.nodes:
            if node.node_id == 0:
                continue # Skip attacker node (runs locally)

            # Simple IP assignment scheme based on Node ID
            ip_addr = f"192.168.56.{100 + node.node_id}"
            machine_name = node.name.lower().replace(" ", "_")

            lines.extend([
                "",
                f"  config.vm.define '{machine_name}' do |{machine_name}|",
                f"    {machine_name}.vm.hostname = '{machine_name}'",
                f"    {machine_name}.vm.network 'private_network', ip: '{ip_addr}'",
                "  end"
            ])

        lines.append("end\n")

        with open(os.path.join(self.build_dir, "Vagrantfile"), "w") as f:
            f.write("\n".join(lines))

    def _generate_ansible_inventory(self, topology: Topology):
        """Generates inventory.ini for Ansible."""
        lines = []
        for node in topology.nodes:
            if node.node_id == 0:
                continue

            ip_addr = f"192.168.56.{100 + node.node_id}"
            machine_name = node.name.lower().replace(" ", "_")

            # Group nodes by their name (e.g., [webserver])
            lines.append(f"[{machine_name}]")
            lines.append(f"{ip_addr} ansible_user=vagrant ansible_ssh_private_key_file=.vagrant/machines/{machine_name}/virtualbox/private_key")
            lines.append("")

        with open(os.path.join(self.build_dir, "inventory.ini"), "w") as f:
            f.write("\n".join(lines))

    def _generate_ansible_playbook(self, topology: Topology):
        """Generates site.yml matching CVEs to Ansible roles."""
        lines = [
            "---",
            "# Forge-Z3 Auto-Generated Cyber Range Playbook",
        ]

        # Group vulnerabilities by node
        node_vulns = {}
        for vuln in topology.vulnerabilities:
            if vuln.node_id not in node_vulns:
                node_vulns[vuln.node_id] = []
            node_vulns[vuln.node_id].append(vuln.cve_id)

        for node in topology.nodes:
            if node.node_id == 0:
                continue

            machine_name = node.name.lower().replace(" ", "_")

            lines.extend([
                "",
                f"- name: Provision {node.name}",
                f"  hosts: {machine_name}",
                "  become: yes",
                "  roles:"
            ])

            # Assign roles based on CVEs
            if node.node_id in node_vulns:
                for cve_id in node_vulns[node.node_id]:
                    # The role name is the CVE ID itself
                    safe_cve_name = cve_id.lower().replace("-", "_")
                    lines.append(f"    - {safe_cve_name}")
            else:
                lines.append("    - common_setup # No vulnerabilities assigned")

        with open(os.path.join(self.build_dir, "site.yml"), "w") as f:
            f.write("\n".join(lines) + "\n")
