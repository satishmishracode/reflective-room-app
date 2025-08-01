"""A simple calculator module."""

from __future__ import annotations

import argparse


def add(a: float, b: float) -> float:
    """Return the sum of *a* and *b*."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Return the difference of *a* minus *b*."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Return the product of *a* and *b*."""
    return a * b


def divide(a: float, b: float) -> float:
    """Return *a* divided by *b*.

    Raises
    ------
    ValueError
        If *b* is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def main(argv: list[str] | None = None) -> None:
    """Run a small CLI for the calculator."""
    parser = argparse.ArgumentParser(description="Simple calculator")
    parser.add_argument("a", type=float, help="First number")
    parser.add_argument("operation", choices=["add", "sub", "mul", "div"],
                        help="Operation to perform")
    parser.add_argument("b", type=float, help="Second number")
    args = parser.parse_args(argv)

    operations = {
        "add": add,
        "sub": subtract,
        "mul": multiply,
        "div": divide,
    }
    result = operations[args.operation](args.a, args.b)
    print(result)


if __name__ == "__main__":
    main()
