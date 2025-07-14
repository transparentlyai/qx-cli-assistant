#!/usr/bin/env python3
"""
Helper module with a function to multiply an arbitrary number of values.
"""


def multiply_numbers(*numbers):
    """
    Multiply an arbitrary number of values together.

    Args:
        *numbers: Variable length argument list of numbers to multiply (can be float, int, or string representations of numbers)

    Returns:
        float: The product of all provided numbers
    """
    return eval("*".join(str(float(num)) for num in numbers) or "1")
