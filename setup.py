from setuptools import setup, find_packages

# Read the contents of the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="omnihub",
    version="1.0.0",
    description="Enterprise Multi-Agent Simulated Workspace with local LLMs and a Self-Learning Feedback Loop.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OmniHub Team",
    url="https://github.com/cheekyclaps/omnihub",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "omnihub": ["config/*.yaml", "config/agents/*.md"],
    },
    install_requires=[
        "crewai==0.11.2",
        "langchain==0.1.20",
        "langchain-community==0.0.38",
        "pydantic>=2.0",
        "rich>=13.0",
        "prompt_toolkit>=3.0",
        "pyyaml",
        "python-dotenv",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "omnihub=omnihub.cli:run_interactive_cli",
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
