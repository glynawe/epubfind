import setuptools
from pathlib import Path

setuptools.setup(
    name="epubfind-glynawe",
    version="1.0.1",
    author="Glyn Webster",
    author_email="glynawe@gmail.com",
    url='',
    description="Searches for phrases within EPUB ebook files.",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "epubfind"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.7",
    install_requires="lxml",
    entry_points={'console_scripts': ['epubfind=epubfind:main']},
    include_package_data=True,
)
