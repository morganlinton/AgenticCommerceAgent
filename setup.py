from setuptools import find_packages, setup


setup(
    name="agentic-shopping-agent",
    version="0.1.0",
    description="A simple shopping agent that uses Browser Use to research products and recommend what to buy.",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "browser-use-sdk>=3.0.0",
        "pydantic>=2.7,<3",
        "python-dotenv>=1.0,<2",
    ],
    extras_require={
        "dev": ["pytest>=8,<9"],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={
        "console_scripts": [
            "shop-agent=agentic_shopping_agent.cli:main",
            "shop-agent-eval=agentic_shopping_agent.eval_cli:main",
            "shop-agent-web=agentic_shopping_agent.web_cli:main",
        ],
    },
)
