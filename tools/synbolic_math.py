from sympy import *
import re


# Enable pretty printing (optional, for debugging)
init_printing(use_unicode=True)


def solve_equation(equation: str) -> str:
    """
    Solve algebraic equation. Example: "x**2 - 4 = 0" → [2, -2]
    """
    try:
        lhs, rhs = equation.split("=")
        expr = parse_expr(lhs) - parse_expr(rhs)
        x = symbols("x")
        solution = solve(expr, x)
        return str(solution)
    except Exception as e:
        return f"Error: {str(e)}"


def differentiate(expression: str, variable: str = "x") -> str:
    """
    Compute derivative of expression w.r.t. variable.
    Example: "x**3 + 2*x", "x" → "3*x**2 + 2"
    """
    try:
        expr = parse_expr(expression)
        var = symbols(variable)
        result = diff(expr, var)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def integrate_expression(expression: str, variable: str = "x") -> str:
    """
    Compute indefinite integral.
    Example: "3*x**2", "x" → "x**3"
    """
    try:
        expr = parse_expr(expression)
        var = symbols(variable)
        result = integrate(expr, var)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def matrix_operation(matrix_a: list, operation: str, matrix_b: list = None) -> str:
    """
    Perform matrix operations: 'determinant', 'inverse', 'transpose', 'multiply'
    matrix_a and matrix_b are list of lists, e.g., [[1,2],[3,4]]
    """
    try:
        A = Matrix(matrix_a)
        if operation == "determinant":
            return str(A.det())
        elif operation == "inverse":
            return str(A.inv())
        elif operation == "transpose":
            return str(A.T)
        elif operation == "multiply" and matrix_b is not None:
            B = Matrix(matrix_b)
            return str(A * B)
        else:
            return "Error: Unsupported operation or missing matrix."
    except Exception as e:
        return f"Error: {str(e)}"


def preprocess_math(expr: str) -> str:
    """Convert common math expressions to Python/sympy syntax"""
    expr = expr.replace("^", "**")
    expr = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", expr)  # 2x → 2*x
    expr = re.sub(r"(\w)(\()", r"\1*(", expr)  # x(2+x) → x*(2+x)
    expr = re.sub(r"(\d)%", r"0.\1", expr)  # 15% → 0.15
    expr = expr.replace(" ", "")  # remove spaces
    return expr


def calculate(expression: str) -> str:
    """
    Safely evaluate basic and advanced math expressions using sympy.
    Supports: +, -, *, /, **, %, parentheses, variables, functions (sin, log, etc.)
    """
    try:
        # Preprocess input
        raw_expr = preprocess_math(expression.strip())

        # Handle percentage usage like "15% of 200"
        if "of" in raw_expr:
            raw_expr = raw_expr.replace("of", "*")

        # Parse and evaluate
        expr = parse_expr(raw_expr, evaluate=True)
        # Try to simplify or evaluate numerically
        result = simplify(expr)

        # If it's a number, show decimal; otherwise keep symbolic
        try:
            float_result = float(result)
            if float_result.is_integer():
                return str(int(float_result))
            return f"{float_result:.6g}"  # Compact float
        except:
            return str(result)  # Keep symbolic: e.g., sqrt(2)

    except Exception as e:
        return f"Error: {str(e)}"
