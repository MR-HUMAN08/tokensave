from setuptools import setup, find_packages

setup(
    name="paisa",
    version="0.1.8",
    description="Smart LLM routing that saves you money — works on Windows, Mac, and Linux",
    packages=find_packages(),
    install_requires=[
        "litellm",
        "python-dotenv",
        "platformdirs",
        "requests",
    ],
    classifiers=[
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "paisa=paisa.cli:main",
        ],
    },
    python_requires=">=3.10",
)
