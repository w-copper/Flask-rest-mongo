from setuptools import Extension, dist, find_packages, setup


setup(
    name='flask-rest-mongo-CopperW',
    version='0.1.0',
    description='Helper utils for mongoDB in flask use flask-rest',
    keywords='flask,mongoDB,restful',
    packages=['flask-rest-mongo'],
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
        'json',
        'Flask',
        'flask-mongoengine',
        'mongoengine',
        'flask-restful'
    ],
    python_requires='>=3.7',
    zip_safe=False
)