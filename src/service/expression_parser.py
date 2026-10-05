"""
Safe mathematical expression parser and evaluator.
Implements Shunting-yard algorithm to convert infix to postfix (RPN),
then evaluates the RPN. Does NOT use eval() or exec().
"""

from typing import List


class ExpressionError(Exception):
    """Raised when the expression is invalid."""
    pass


class ExpressionParser:
    # Operator precedence: higher number = higher precedence
    PRECEDENCE = {
        '+': 1,
        '-': 1,
        '*': 2,
        '/': 2,
        'u-': 3,  # unary minus
        'u+': 3,  # unary plus
    }

    OPERATORS = set('+-*/()')

    def tokenize(self, expression: str) -> List[str]:
        """Convert a string expression into a list of tokens."""
        tokens = []
        i = 0
        n = len(expression)
        prev_token = None

        while i < n:
            ch = expression[i]

            # Skip whitespace
            if ch.isspace():
                i += 1
                continue

            # Numbers (including decimals)
            if ch.isdigit() or ch == '.':
                j = i
                dot_count = 0
                while j < n and (expression[j].isdigit() or expression[j] == '.'):
                    if expression[j] == '.':
                        dot_count += 1
                    j += 1
                if dot_count > 1:
                    raise ExpressionError("Invalid number: multiple decimal points")
                tokens.append(expression[i:j])
                i = j
                prev_token = 'num'
                continue

            # Operators and parentheses
            if ch in self.OPERATORS:
                # Detect unary minus/plus
                if ch in '+-' and (
                    prev_token is None
                    or prev_token == 'op'
                    or prev_token == '('
                ):
                    if ch == '-':
                        tokens.append('u-')
                    else:
                        tokens.append('u+')
                else:
                    tokens.append(ch)
                prev_token = 'op'
                i += 1
                continue

            raise ExpressionError(f"Invalid character: '{ch}' at position {i}")

        return tokens

    def to_rpn(self, tokens: List[str]) -> List[str]:
        """Convert infix tokens to Reverse Polish Notation using Shunting-yard."""
        output = []
        stack = []

        for token in tokens:
            # Number
            if token not in self.OPERATORS and token not in ('u-', 'u+'):
                output.append(token)
            # Left parenthesis
            elif token == '(':
                stack.append(token)
            # Right parenthesis
            elif token == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if not stack:
                    raise ExpressionError("Mismatched parentheses")
                stack.pop()  # remove '('
            # Operator
            else:
                while stack and stack[-1] != '(' and (
                    self.PRECEDENCE.get(stack[-1], 0) >= self.PRECEDENCE.get(token, 0)
                ):
                    output.append(stack.pop())
                stack.append(token)

        while stack:
            if stack[-1] == '(':
                raise ExpressionError("Mismatched parentheses")
            output.append(stack.pop())

        return output

    def eval_rpn(self, rpn: List[str]) -> float:
        """Evaluate a Reverse Polish Notation expression."""
        stack = []

        for token in rpn:
            if token not in self.PRECEDENCE:
                # It's a number
                stack.append(float(token))
            else:
                # Unary operators
                if token in ('u-', 'u+'):
                    if not stack:
                        raise ExpressionError("Invalid expression")
                    val = stack.pop()
                    if token == 'u-':
                        stack.append(-val)
                    else:
                        stack.append(val)
                # Binary operators
                else:
                    if len(stack) < 2:
                        raise ExpressionError("Invalid expression")
                    b = stack.pop()
                    a = stack.pop()
                    if token == '+':
                        stack.append(a + b)
                    elif token == '-':
                        stack.append(a - b)
                    elif token == '*':
                        stack.append(a * b)
                    elif token == '/':
                        if b == 0:
                            raise ExpressionError("Division by zero")
                        stack.append(a / b)

        if len(stack) != 1:
            raise ExpressionError("Invalid expression")

        return stack[0]

    def calculate(self, expression: str):
        """Parse and calculate a mathematical expression."""
        if not expression or not expression.strip():
            raise ExpressionError("Empty expression")

        tokens = self.tokenize(expression)
        if not tokens:
            raise ExpressionError("Empty expression")

        rpn = self.to_rpn(tokens)
        result = self.eval_rpn(rpn)

        # Return integer if it's a whole number
        if result == int(result):
            return int(result)
        return round(result, 10)
