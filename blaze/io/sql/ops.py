"""SQL implementations of element-wise ufuncs."""

from __future__ import absolute_import, division, print_function

from ...compute.function import function, kernel
from ...compute.ops import ufuncs
from .kernel import sql_kernel, SQL
from .syntax import Call, Expr, QOrderBy, QWhere, And, Or, Not


def sqlfunction(signature):
    def decorator(f):
        blaze_func = function(signature)(f)
        kernel(blaze_func, SQL, f, signature)
        return blaze_func
    return decorator


def define_unop(signature, name, op):
    """Define a unary sql operator"""
    def unop(x):
        return Expr([op, x])
    unop.__name__ = name
    _implement(unop, signature)
    return unop


def define_binop(signature, name, op):
    """Define a binary sql operator"""
    def binop(a, b):
        return Expr([a, op, b])
    binop.__name__ = name
    _implement(binop, signature)
    return binop


def _implement(f, signature):
    name = f.__name__
    blaze_func = getattr(ufuncs, name)
    #print("implement", f, signature, blaze_func)
    sql_kernel(blaze_func, f, signature)

# Arithmetic

add = define_binop("A -> A -> A", "add", "+")
multiply = define_binop("A -> A -> A", "multiply", "*")
subtract = define_binop("A -> A -> A", "subtract", "-")
floordiv = define_binop("A -> A -> A", "floor_divide", "/")
divide = define_binop("A -> A -> A", "divide", "/")
truediv = define_binop("A -> A -> A", "true_divide", "/")
mod = define_binop("A -> A -> A", "mod", "%")

negative = define_unop("A -> A", "negative", "-")

# Compare

eq = define_binop("A..., T -> A..., T -> A..., bool", "equal", "==")
ne = define_binop("A..., T -> A..., T -> A..., bool", "not_equal", "!=")
lt = define_binop("A..., T -> A..., T -> A..., bool", "less", "<")
le = define_binop("A..., T -> A..., T -> A..., bool", "less_equal", "<=")
gt = define_binop("A..., T -> A..., T -> A..., bool", "greater", ">")
ge = define_binop("A..., T -> A..., T -> A..., bool", "greater_equal", ">=")

# Logical

logical_and = define_binop("A..., bool -> A..., bool -> A..., bool",
                           "logical_and", "AND")
logical_or  = define_binop("A..., bool -> A..., bool -> A..., bool",
                           "logical_or", "OR")
logical_not = define_unop("A..., bool -> A..., bool", "logical_not", "NOT")

def logical_xor(a, b):
    # Potential exponential code generation...
    return And(Or(a, b), Not(And(a, b)))

kernel(ufuncs.logical_xor, SQL, logical_xor,
       "A..., bool -> A..., bool -> A..., bool")

# SQL Functions

@sqlfunction('A, DType -> DType')
def sum(col):
    return Call('SUM', [col])

@sqlfunction('A, DType -> DType')
def avg(col):
    return Call('AVG', [col])

@sqlfunction('A, DType -> DType')
def min(col):
    return Call('MIN', [col])

@sqlfunction('A, DType -> DType')
def max(col):
    return Call('MAX', [col])

# SQL Join, Where, Group by, Order by

def merge(left, right, how='left', on=None, left_on=None, right_on=None,
          left_index=False, right_index=False, sort=True):
    """
    Join two tables.
    """
    raise NotImplementedError


def index(col, index, order=None):
    """
    Index a table or column with a predicate.

        view = merge(table1, table2)
        result = view[table1.id == table2.id]

    or

        avg(table1.age[table1.state == 'TX'])
    """
    result = sqlindex(col, index)
    if order:
        result = sqlorder(result, order)
    return result


@sqlfunction('A -> B -> A')
def sqlindex(col, where):
    return QWhere(col, where)

@sqlfunction('A -> B -> A')
def sqlorder(col, by):
    if not isinstance(by, (tuple, list)):
        by = [by]
    return QOrderBy(col, by)
