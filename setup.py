from setuptools import setup, find_packages

VERSION = "1.0.0"


def readme():
    with open('README.md', encoding="utf8") as f:
        return f.read()

setup(
    name="card-automation-server",
    version=VERSION,
    description="WinDSX Card Automation Server",
    long_description=readme(),
    long_description_content_type='text/markdown',
    author="Justin Nesselrotte",
    author_email="admin@jnesselr.org",
    license="MIT",
    url="https://github.com/card-automation/card-server",
    install_requires=[
        "githubkit",
        "platformdirs",
        "psutil",
        "pyodbc",
        "pytest",
        "requests",
        "sentry-sdk==2.8.0",
        "SQLAlchemy",
        "sqlalchemy-access",
        "tomlkit",
        "watchdog",
    ],
    packages=find_packages(include=['card_automation_server', 'card_automation_server.*']),
    classifiers=[
        'License :: OSI Approved :: MIT License',
    ]
)
