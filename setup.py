import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="seliky",
    version="5.3.2",
    author="TEARK",
    author_email="913355434@qq.com",
    description="a better ui autotest lib based on selenium, compatible with robot framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitee.com/teark/seliky.git",
    packages=setuptools.find_packages(),
    install_requires=[
        'selenium >= 4.5.0',
        'pywin32'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
