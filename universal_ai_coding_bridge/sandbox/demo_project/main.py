"""
Main entry point for demo project
"""

from calculator import add, subtract, multiply, divide, power


def main():
    """Run demo calculations"""
    print("Demo Calculator")
    print("=" * 40)
    
    a, b = 10, 5
    
    print(f"\nTesting with a={a}, b={b}")
    print(f"add({a}, {b}) = {add(a, b)}")
    print(f"subtract({a}, {b}) = {subtract(a, b)}")
    print(f"multiply({a}, {b}) = {multiply(a, b)}")
    print(f"divide({a}, {b}) = {divide(a, b)}")
    print(f"power({a}, {b}) = {power(a, b)}")
    
    # Test edge case
    print("\nEdge case: divide(10, 2)")
    result = divide(10, 2)
    print(f"Result: {result}")
    
    if result == 5:
        print("✓ PASS: Division is correct")
    else:
        print(f"✗ FAIL: Expected 5, got {result}")


if __name__ == "__main__":
    main()
