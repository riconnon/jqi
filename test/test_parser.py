import pytest
from jqi.parser import parse, Token, Field, Ident, term, exp, ParseError
from jqi.error import Error
from jqi.eval import make_env
from jqi import parser


def simplify(x):
    if isinstance(x, str):
        return x.replace(".", "_").replace(" ", "_")
    elif isinstance(x, (list, tuple)):
        return "".join(type(i).__name__[0] for i in x)
    elif isinstance(x, type):
        return x.__name__
    else:
        return type(x).__name__


@pytest.mark.parametrize("input,stream,result", [
    ("", [], ParseError),
    (".", [], []),
    (".", [1, 2, 3], [1, 2, 3]),
    (".a", [1, [1, 2], {"a": "b"}, {}], [Error, Error, "b", None]),
    (".a.b", [{"a": {"b": "c"}}, {}], ["c", None]),
    ("1", [1, 2, 3], [1, 1, 1]),
    ("-1", [1, 2, 3], [-1, -1, -1]),
    ("(1, 2)", [None], [1, 2]),
], ids=simplify)
def test_term(input, stream, result):
    if isinstance(result, type) and issubclass(result, Exception):
        with pytest.raises(result):
            parse(input, start=term)
        return
    assert parse(input, start=term)({}, stream) == ({}, result)


def test_field():
    assert parser.p_field.parse([Field("a")]) == Field("a")


@pytest.mark.parametrize("input,stream,result", [
    ("", [], ParseError),
    (".", [], []),
    (".", [1, 2, 3], [1, 2, 3]),
    (".a", [1, [1, 2], {"a": "b"}, {}], [Error, Error, "b", None]),
    (".|.", [], []),
    (".|.", [1, 2, 3], [1, 2, 3]),
    (".|.|.|.", [1, 2, 3], [1, 2, 3]),
    (".a.b", [{"a": {"b": "c"}}, {}], ["c", None]),
    (".a|.b", [{"a": {"b": "c"}}, {}], ["c", None]),
    ("1, 2", [0, 0], [1, 2, 1, 2]),
    ("1 + 2", [None], [3]),
    ("3 - 1 - 1", [None], [1]),
    ("(1, 2, 3)", [None], [1, 2, 3]),
    ("false", [None], [False]),
    ("true", [None], [True]),
    ("null", [None], [None]),
    ('(false, true)', [None], [False, True]),
    ('(false, true) and (false, true)', [None], [False, False, True]),  # Short-circuits
    ('(true, true) and (false, true)', [None], [False, True, False, True]),
    ('(1, 3) * (4, 7)', [None], [4, 12, 7, 21]),  # Note the ordering: leftmost fastest
    ('(false, true) and (true, false)', [None], [False, True, False]),
    ('(false, true) or (true, false)', [None], [True, False, True]),
    ('1 + 2 * 3', [None], [7]),                 # Check precedence
    ("not", [False, True, 1, [], {}, None], [True, False, False, False, False, True])
], ids=simplify)
def test_exp(input, stream, result):
    if isinstance(result, type) and issubclass(result, Exception):
        with pytest.raises(result):
            parse(input, start=term)
        return
    env = make_env()
    assert parse(input, start=exp)(env, stream) == (env, result)