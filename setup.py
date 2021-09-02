import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="seliky",
    version="0.5",
    author="TEARK",
    author_email="913355434@qq.com",
    description="a better lib based on selenium",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitee.com/teark/seliky.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)