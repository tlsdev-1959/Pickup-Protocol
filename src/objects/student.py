from objects import user
from dataclasses import dataclass


@dataclass
class Student:
    id: int
    first: str
    last: str
    grade: str
    crew: str
    picutre_url: str
    pickups: dict
    visitors: dict
    at_now: dict

    def printName(self):
        return f'{self.first} {self.last}'