import codecs
from setuptools import setup


with codecs.open('readme.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="Hshadow",
    version="0.0.0",
    license='http://www.apache.org/licenses/LICENSE-2.0',
    description="A fast tunnel proxy that help you get through firewalls",
    author='clowwindy',
    author_email='qingluan@gmail.com',
    url='https://github.com/qingluan/iortcp',
    packages=['hshadow'],
    package_data={
        'hshadow': ['LICENSE']
    },
    install_requires=[],
    entry_points="""
    [console_scripts]
    Rio = hshadow.reverse:get_config
    """,
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: Proxy Servers',
    ],
    long_description=long_description,
)
