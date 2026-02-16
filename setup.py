from setuptools import find_packages, setup

setup(
    name="ai-cost-tracker",
    version="0.1.0",
    description="Track LLM API usage and costs per user and feature.",
    long_description=(
        "A lightweight Python library that tracks OpenAI and Anthropic costs "
        "per user and per product feature using a single decorator."
    ),
    long_description_content_type="text/plain",
    author="ai-cost-tracker contributors",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=["openai>=1.0.0", "anthropic>=0.18.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
