from distutils.core import setup

from youmu.manifest import VERSION

setup(
    name='youmu',
    packages=[
        'youmu',
        'youmu.cogs',
        'youmu.embeds',
        'youmu.modules',
        'youmu.reusables'
    ],
    version=VERSION,
    description='The heart of The Mapset Management Server on Discord.',
    author='Kyuunex',
    author_email='kyuunex@protonmail.ch',
    url='https://github.com/Kyuunex/Youmu',
    install_requires=[
        'discord.py[voice]',
        'feedparser',
        'aioosuapi @ git+https://github.com/Kyuunex/aioosuapi.git@v1',
        'aioosuwebapi @ git+https://github.com/Kyuunex/aioosuapi.git@v2'
    ],
)
