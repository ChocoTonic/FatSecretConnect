from setuptools import find_packages, setup

setup(
    name="FatSecretConnect",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4==4.12.2",
        "bs4==0.0.1",
        "certifi==2023.7.22",
        "charset-normalizer==3.3.2",
        "fatsecret==0.4.0",
        "idna==3.4",
        "lxml==4.9.3",
        "pytz==2023.3.post1",
        "rauth==0.7.3",
        "requests==2.31.0",
        "soupsieve==2.5",
        "urllib3==2.0.7",
    ],
    author="ChocoTonic",
    author_email="",
    description="A Python wrapper for the FatSecret API.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ChocoTonic/FatSecretConnect",
)
