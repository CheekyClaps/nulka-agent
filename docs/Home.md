# NulkaAgent Wiki

Welcome to the official Wiki for **NulkaAgent**, the Enterprise Multi-Agent Simulated Workspace.

## Table of Contents
1. [Core Architecture](Architecture.md)
2. [The Self-Learning Feedback Loop (Teacher & Oracle)](Learning-Loop.md)
3. [Customizing Agents](Custom-Agents.md)

## Design Philosophy
NulkaAgent was built on the premise that prompt-engineering should be decoupled from python application logic. To achieve this, NulkaAgent uses a YAML/Markdown split configuration structure. 

All meta configurations are stored in YAML, while long-form instructions, personas, and dynamically updated rules are kept cleanly in Markdown files. 
