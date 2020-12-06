from setuptools import Extension, dist, find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='flask-rest-mongo',
    version='0.1.1',
    description='Helper utils for mongoDB in flask use flask-rest',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/w-copper/Flask-rest-mongo.git",
    keywords='flask,mongoDB,restful',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Utilities',
    ],
    author='Wang Tong',
    author_email='copper.w@foxmail.com',
    install_requires=[
        'Flask',
        'flask-mongoengine',
        'mongoengine',
        'flask-restful'
    ],
    python_requires='>=3.7',
    zip_safe=False
)