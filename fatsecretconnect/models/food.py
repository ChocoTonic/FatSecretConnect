from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Callable, Union


@dataclass
class Food:
    name: str
    weight: float
    calories: float
    fat: float
    carbohydrates: float
    protein: float

    def __str__(self) -> str:
        return f"""name: {self.name}
weight: {self.weight}
calories: {self.calories}
fat: {self.fat}
carbohydrates: {self.carbohydrates}
protein: {self.protein}"""

    def _func(
        self, other: Union[int, float], fun: Callable[[float, Union[int, float]], float]
    ) -> Food:
        if isinstance(other, (int, float)):
            return Food(
                name=self.name,
                weight=fun(self.weight, other),
                calories=fun(self.calories, other),
                fat=fun(self.fat, other),
                carbohydrates=fun(self.carbohydrates, other),
                protein=fun(self.protein, other),
            )
        else:
            return NotImplemented

    def __truediv__(self, other: Union[int, float]) -> Food:
        return self._func(other, operator.truediv)

    def __mul__(self, other: Union[int, float]) -> Food:
        return self._func(other, operator.mul)
