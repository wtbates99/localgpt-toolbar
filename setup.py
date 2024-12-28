from setuptools import setup, find_packages

setup(
    name="toolbar-chat",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.4.0",
        "openai>=1.0.0",
        "python-dotenv>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "toolbar-chat=main:main",
        ],
    },
    python_requires=">=3.8",
)
