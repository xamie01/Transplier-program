"""AST helper utilities for extracting information from Python AST nodes."""
import ast
from typing import Any, Optional


def get_call_name(node: ast.Call) -> Optional[str]:
    """Extract function name from a Call node.
    
    Examples:
        sma(close, 20) -> "sma"
        ta.sma(close, 20) -> "ta.sma" or "sma" depending on attr
    """
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        # e.g., ta.sma -> return "sma" or "ta.sma"
        return node.func.attr
    return None


def literal_value(node: ast.expr) -> Optional[Any]:
    """Extract literal value from an AST node (int, float, str, bool, None)."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Num):  # Python < 3.8
        return node.n
    if isinstance(node, ast.Str):  # Python < 3.8
        return node.s
    if isinstance(node, ast.NameConstant):  # Python < 3.8
        return node.value
    return None


def expr_to_string(node: ast.expr) -> str:
    """Convert an AST expression back to a string (approximate).
    
    Uses ast.unparse if available (Python 3.9+), else falls back to manual stringification.
    """
    try:
        return ast.unparse(node)
    except AttributeError:
        # Fallback for Python < 3.9
        return _unparse_simple(node)


def _unparse_simple(node: ast.expr) -> str:
    """Simple recursive unparse for basic expressions."""
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_unparse_simple(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        func_str = _unparse_simple(node.func)
        args = ", ".join(_unparse_simple(arg) for arg in node.args)
        return f"{func_str}({args})"
    if isinstance(node, ast.BinOp):
        left = _unparse_simple(node.left)
        right = _unparse_simple(node.right)
        op = _binop_to_string(node.op)
        return f"({left} {op} {right})"
    if isinstance(node, ast.Compare):
        left = _unparse_simple(node.left)
        parts = [left]
        for op, comp in zip(node.ops, node.comparators):
            parts.append(_cmpop_to_string(op))
            parts.append(_unparse_simple(comp))
        return " ".join(parts)
    return repr(node)


def _binop_to_string(op: ast.operator) -> str:
    """Convert binary operator to string."""
    mapping = {
        ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
        ast.Mod: "%", ast.Pow: "**", ast.FloorDiv: "//",
        ast.BitAnd: "&", ast.BitOr: "|", ast.BitXor: "^",
    }
    return mapping.get(type(op), str(op))


def _cmpop_to_string(op: ast.cmpop) -> str:
    """Convert comparison operator to string."""
    mapping = {
        ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
        ast.Gt: ">", ast.GtE: ">=", ast.Is: "is", ast.IsNot: "is not",
        ast.In: "in", ast.NotIn: "not in",
    }
    return mapping.get(type(op), str(op))


def find_calls(tree: ast.AST, func_names: list = None) -> list:
    """Find all Call nodes in an AST, optionally filtered by function name."""
    calls = []

    class CallFinder(ast.NodeVisitor):
        def visit_Call(self, node):
            if func_names is None:
                calls.append(node)
            else:
                name = get_call_name(node)
                if name:
                    lname = name.lower()
                    if any(lname.endswith(fn.lower()) or lname == fn.lower() for fn in func_names):
                        calls.append(node)
                else:
                    # no name extracted
                    pass
            
            self.generic_visit(node)

    CallFinder().visit(tree)
    return calls


def find_assignments(tree: ast.AST, var_names: list = None) -> list:
    """Find all assignment nodes, optionally filtered by target variable name."""
    assigns = []

    class AssignFinder(ast.NodeVisitor):
        def visit_Assign(self, node):
            if var_names is None:
                assigns.append(node)
            else:
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in var_names:
                        assigns.append(node)
                        break
            self.generic_visit(node)

    AssignFinder().visit(tree)
    return assigns
