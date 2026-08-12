"""
Demo project for UACB testing

Contains intentional bugs that can be fixed by the AI agent.
"""

# calculator.py - Has a bug in division


def add(a, b):
    """Add two numbers"""
    return a + b


def subtract(a, b):
    """Subtract b from a"""
    return a - b


def multiply(a, b):
    """Multiply two numbers"""
    return a * b


def divide(a, b):
    """Divide a by b
    
    BUG: This has an off-by-one error for testing
    """
    # BUG: Should be a / b, not (a + 1) / b
    return (a + 1) / b  # Intentional bug for E2E testing


def power(a, b):
    """Raise a to the power of b"""
    return a ** b
