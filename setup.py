#!/usr/bin/env python3
"""
Setup script for Sims 4 Mod Conflict Detector
"""

from setuptools import setup, find_packages

setup(
    name="sims4_mod_conflict_detector",
    version="1.0.0",
    description="Tool to detect conflicts between mods in The Sims 4",
    author="Community Project",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mod_conflict_detector=mod_conflict_detector:main',
        ],
    },
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)