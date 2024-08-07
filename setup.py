from setuptools import setup, find_packages

setup(
    name="ResumeGPT",
    version="1.4",
    description="A brief description of your project",
    author="Tyler Kline",
    author_email="tylerkline@gmail.com",
    url="https://github.com/takline/ResumeGPT",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.9.3",
        "configparser>=5.0.2",
        "langchain==0.1.20",
        "langchain-openai==0.1.6",
        "langchain-core==0.1.52",
        "pydantic==2.7.1",
        "reportlab>=3.5.59",
        "requests>=2.25.1",
        "ruamel.yaml>=0.16.12",
        "pytest>=8.2.2",
        "free-proxy>=1.1.1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
