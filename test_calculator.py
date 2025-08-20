import unittest
import calculator

class TestCalculator(unittest.TestCase):
    def test_add_positive(self):
        self.assertEqual(calculator.add(2, 3), 5)
    def test_add_negative(self):
        self.assertEqual(calculator.add(-2, -3), -5)
    def test_add_zero(self):
        self.assertEqual(calculator.add(0, 5), 5)
    def test_add_float(self):
        self.assertEqual(calculator.add(2.5, 3.5), 6.0)

if __name__ == '__main__':
    unittest.main()