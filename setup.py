from setuptools import setup, find_packages

# Read the contents of the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="omniagent",
    version="1.0.0",
    description="Enterprise Multi-Agent Simulated Workspace with local LLMs and a Self-Learning Feedback Loop.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OmniAgent Team",
    url="https://github.com/cheekyclaps/omniagent",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "omniagent": ["config/*.yaml", "config/agents/*.md"],
    },
    install_requires=[
        "crewai",
        "langchain",
        "langchain-community",
        "pydantic>=2.0",
        "rich>=13.0",
        "prompt_toolkit>=3.0",
        "pyyaml",
        "python-dotenv",
        "requests",
        "ddgs",
        "beautifulsoup4"
    ],
    entry_points={
        "console_scripts": [
            "omniagent=omniagent.cli:run_interactive_cli",
        ],
    },
    python_requires=">=3.10",
    keywords="ai, agents, crewai, ollama, llm, gemini, cli, multi-agent, autonomous, self-learning, developer tools, oracle",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
