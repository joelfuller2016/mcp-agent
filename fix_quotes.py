#!/usr/bin/env python3
"""Fix escaped quotes in Python files."""

import re

# Read the file
with open(
    "src/mcp_agent/autonomous/adaptive_orchestrator.py", "r", encoding="utf-8"
) as f:
    content = f.read()

# Replace escaped quotes with normal quotes
# This handles \" -> "
fixed_content = content.replace('\\"', '"')

# Write back the fixed content
with open(
    "src/mcp_agent/autonomous/adaptive_orchestrator.py", "w", encoding="utf-8"
) as f:
    f.write(fixed_content)

print("Fixed escaped quotes in adaptive_orchestrator.py")
