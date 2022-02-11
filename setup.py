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
    description='An osu! Discord bot that posts newly ranked maps, NAT/BN changes, or map uploads of users you track.',
    author='Kyuunex',
    author_email='kyuunex@protonmail.ch',
    url='https://github.com/Kyuunex/Youmu',
    install_requires=[
        'discord.py[voice]==1.7.3',
        'feedparser',
        'aioosuapi @ git+https://github.com/Kyuunex/aioosuapi.git@1.2.1',
        'aioosuwebapi @ git+https://github.com/Kyuunex/aioosuapi.git@2.0.0-placeholder.5',
        'psutil',
        'aiohttp'
    ],
)
