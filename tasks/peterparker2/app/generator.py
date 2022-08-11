from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO
import operator
import random
import subprocess
import tempfile
import sys


COMPLEXITY = 20
BULK = 100


class Sub(ABC):
    children: list[Sub]

    @abstractmethod
    def clone(self, frac_nesting: int) -> Sub:
        pass


class NoneSub(Sub):
    def __init__(self):
        self.value = random.randint(0, 9)

    def clone(self, frac_nesting: int):
        return type(self)()

    def to_latex(self, add_parentheses_starting_with_precedence: int):
        return str(self.value)

    def compute(self) -> float:
        return self.value


class Space:
    def __init__(self, frac_nesting: int):
        self.sub: Sub = NoneSub()
        self.frac_nesting: int = frac_nesting


class Binary(Sub):
    def __init__(self, op: str, precedence: int, associative: bool, fn: Callable[[float, float], float], frac_nesting: int):
        self.children = [Space(frac_nesting), Space(frac_nesting)]
        self.op = op
        self.precedence = precedence
        self.associative = associative
        self.fn = fn

    def clone(self, frac_nesting: int):
        return type(self)(self.op, self.precedence, self.associative, self.fn, frac_nesting)

    def to_latex(self, add_parentheses_starting_with_precedence: int):
        l = self.children[0].sub.to_latex(self.precedence + 1)
        r = self.children[1].sub.to_latex(self.precedence + self.associative)
        s = f"{l} {self.op} {r}"
        if self.precedence >= add_parentheses_starting_with_precedence:
            s = f"\\left({s}\\right)"
        return s

    def compute(self) -> float:
        return self.fn(self.children[0].sub.compute(), self.children[1].sub.compute())


class Frac(Sub):
    def __init__(self, frac_nesting: int):
        self.children = [Space(frac_nesting), Space(frac_nesting)]

    def clone(self, frac_nesting: int):
        return type(self)(frac_nesting)

    def to_latex(self, add_parentheses_starting_with_precedence: int):
        l = self.children[0].sub.to_latex(4)
        r = self.children[1].sub.to_latex(4)
        s = f"\\frac{{{l}}}{{{r}}}"
        if add_parentheses_starting_with_precedence == 4:
            s = f"\\left({s}\\right)"
        return s

    def compute(self) -> float:
        return self.children[0].sub.compute() / self.children[1].sub.compute()


SUBS = [
    Binary("\\cdot", 1, True, operator.mul, 0),
    Binary("+", 2, True, operator.add, 0),
    Binary("-", 2, False, operator.sub, 0)
]
SUB_FRAC = Frac(0)


class Generator:
    def __init__(self):
        self.root: Space = Space(0)
        self.spaces: list[Space] = [self.root]


    def replace_space(self):
        space = random.choice(self.spaces)
        del self.spaces[self.spaces.index(space)]
        if space.frac_nesting == 0:
            sub = random.choice(SUBS + [SUB_FRAC])
        else:
            sub = random.choice(SUBS)
        space.sub = sub.clone(space.frac_nesting + isinstance(sub, Frac))
        self.spaces += space.sub.children


    def generate(self) -> tuple[str, int]:
        for _ in range(COMPLEXITY):
            self.replace_space()
        return self.root.sub.to_latex(100), self.root.sub.compute()


def generate() -> tuple[bytes, float]:
    try:
        eq, val = Generator().generate()
        if abs(round(val) - val) < 0.01:
            raise ZeroDivisionError
        return eq, val
    except ZeroDivisionError:
        return generate()


def generate_rendered_bulk() -> list[tuple[bytes, float]]:
    tex = r"\documentclass[multi,varwidth,12pt]{standalone}\begin{document}"
    vals = []
    for _ in range(BULK):
        eq, val = generate()
        tex += r"\[" + eq + r"\] \newpage "
        vals.append(val)
    tex += r"\end{document}"

    with tempfile.TemporaryDirectory() as workdir:
        with open(f"{workdir}/formulae.tex", "w") as f:
            f.write(tex)
        subprocess.run(["latex", "-halt-on-error", "-interaction=nonstopmode", "formulae.tex"], cwd=workdir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["dvipng", "-T", "tight", "-D", "150", "formulae.dvi"], cwd=workdir, check=True, stdout=subprocess.DEVNULL)

        pics = []
        for i in range(BULK):
            with open(f"{workdir}/formulae{i + 1}.png", "rb") as f:
                pics.append(f.read())

    return list(zip(pics, vals))


prerendered = []

def generate_rendered() -> tuple[bytes, int]:
    if not prerendered:
        prerendered.extend(generate_rendered_bulk())
    return prerendered.pop()
