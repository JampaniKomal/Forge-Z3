# Key Tools & Repositories Reference

A quick-reference list of every tool, repo, and paper discovered in the deep research sweep. Use this to explore each one further.

---

## Vulnerability Compilers (Layer 1)
| Name | Link | Notes |
|---|---|---|
| SecGen | https://github.com/cliffe/SecGen | The gold standard. Ruby + Vagrant + Puppet. XML-based. |
| Metarget | https://github.com/metarget/metarget | Kubernetes/cloud-native vulnerable envs. |
| DumpsterFire | https://github.com/TryCatchHCF/DumpsterFire | Log/incident simulation, not VM provisioning. |

## Topology Builders (Layer 2)
| Name | Link | Notes |
|---|---|---|
| AE3GIS Paper | https://mdpi.com | Cyber range topology builder → JSON → GNS3. |
| Topolizer | https://github.com (search: topolizer) | Drag-and-drop, JSON export. |
| NetJSON Spec | https://netjson.org | Data interchange standard for network topologies. |
| CyberBattleSim | https://github.com/microsoft/CyberBattleSim | Microsoft RL simulation. Graph-based attack/defense. |

## Formal Verification (SMT Layer)
| Name | Link | Notes |
|---|---|---|
| Z3 Python API | https://github.com/Z3Prover/z3 | Core tool. `pip install z3-solver`. |
| Z3 FirewallChecker | https://github.com/Z3Prover/FirewallChecker | Firewall rule equivalence verification example. |
| VSDL Paper | https://arxiv.org (search: VSDL cyber range SMT) | Formal language for cyber range specs. Uses SMT. Closest prior art to this project. |
| IAMSpy | https://github.com (search: IAMSpy Z3) | Uses Z3 for AWS IAM policy analysis. |

## LLM Attack Graph Research (Neural Layer)
| Name | Link | Notes |
|---|---|---|
| PentestGPT | https://github.com/GreyDGL/PentestGPT | Autonomous pentest agent. Reasoning+Generation+Parsing modules. |
| AttackGen | https://github.com/mrwadams/attackgen | LLM + MITRE ATT&CK → incident response scenarios. |
| GARAGE Paper | https://arxiv.org (search: GARAGE attack graph RAG) | RAG + LLM for attack graph from CTI. |
| AttacKG | https://github.com (search: AttacKG attack graph) | LLM + NLP → knowledge-enhanced attack graphs. |
| Attack Flow | https://github.com/center-for-threat-informed-defense/attack-flow | MITRE-led. Models adversary action sequences. |

## Neuro-Symbolic AI Reference
| Name | Link | Notes |
|---|---|---|
| NeSy in Cybersecurity Survey | https://github.com/ShamaSharma/Charting-the-evolurtion-of-Neuro-symbolic-AI-in-cybersecurity | Comprehensive paper + repo index. |
| ProofOfThought | https://github.com (search: ProofOfThought LLM Z3) | LLM + Z3 integration for logical verification. |

## Infrastructure as Code (Output Layer)
| Name | Link | Notes |
|---|---|---|
| SecGen Scenarios | https://github.com/cliffe/SecGen/tree/master/scenarios | Example XML outputs to study. |
| Terraform Docs | https://developer.hashicorp.com/terraform | Alternative output target (HCL format). |
| Ansible | https://docs.ansible.com | Another IaC output target for VM provisioning. |
