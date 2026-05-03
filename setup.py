from setuptools import setup, find_packages

setup(
    name="paisa",
    version="0.1.0",
    description="Intelligent LLM routing — classify locally, compress with TOON, route to the fastest free model",
    packages=find_packages(),
    install_requires=[
        "litellm",
        "sentence-transformers",
        "python-dotenv",
        "torch",
        "fastapi",
        "uvicorn",
    ],
    entry_points={
        "console_scripts": [
            "paisa=paisa.cli:main",
        ],
    },
    python_requires=">=3.10",
)
