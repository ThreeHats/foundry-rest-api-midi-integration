#!/usr/bin/env python3
# version.py - Application version information
"""
Application version information.
This file is used by both the build system and the update checker.
"""

# Version information
VERSION = "0.0.1"
VERSION_INFO = (0, 0, 1)

# Repository information
GITHUB_REPO = "ThreeHats/foundry-rest-api-midi-integration"

# Application metadata
APP_NAME = "MIDI-REST-Integration"
APP_DESCRIPTION = "MIDI to REST API Integration Tool"
APP_AUTHOR = "Noah"

def get_version():
    """Get the current version string."""
    return VERSION

def get_version_info():
    """Get the current version as a tuple."""
    return VERSION_INFO

def get_github_repo():
    """Get the GitHub repository name."""
    return GITHUB_REPO
