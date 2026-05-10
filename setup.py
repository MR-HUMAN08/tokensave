from setuptools import setup, find_packages

setup(
    name="paisa",
    version="0.1.7",
    description="Paisa — smart LLM routing that saves you money",
    packages=find_packages(),
    install_requires=[
        "litellm",
        "python-dotenv",
        "platformdirs",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "paisa=paisa.cli:main",
        ],
    },
    python_requires=">=3.10",
)
