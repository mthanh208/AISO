"""Tests for calculator module"""

import pytest
from calculator import add, subtract, multiply, divide, power


class TestAdd:
    def test_add_positive(self):
        assert add(2, 3) == 5
    
    def test_add_negative(self):
        assert add(-1, -1) == -2
    
    def test_add_zero(self):
        assert add(0, 0) == 0


class TestSubtract:
    def test_subtract_positive(self):
        assert subtract(5, 3) == 2
    
    def test_subtract_negative(self):
        assert subtract(-1, -1) == 0


class TestMultiply:
    def test_multiply_positive(self):
        assert multiply(3, 4) == 12
    
    def test_multiply_zero(self):
        assert multiply(5, 0) == 0


class TestDivide:
    def test_divide_even(self):
        """Test even division"""
        assert divide(10, 2) == 5  # Will fail with bug
    
    def test_divide_odd(self):
        """Test odd division"""
        assert divide(9, 3) == 3  # Will fail with bug
    
    def test_divide_float(self):
        """Test float result"""
        assert divide(7, 2) == 3.5  # Will fail with bug


class TestPower:
    def test_power_positive(self):
        assert power(2, 3) == 8
    
    def test_power_zero(self):
        assert power(5, 0) == 1
