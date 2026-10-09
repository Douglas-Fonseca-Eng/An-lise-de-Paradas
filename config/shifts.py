"""
Turnos da planta.

Cada turno tem nome, início (inclusivo) e fim (exclusivo).
Um turno que termina "antes" de começar (fim < início) atravessa a meia-noite.
"""
from datetime import time

TURNOS = [
    {"nome": "A", "inicio": time(5, 30), "fim": time(14, 30)},
    {"nome": "B", "inicio": time(14, 30), "fim": time(22, 30)},
    {"nome": "C", "inicio": time(22, 30), "fim": time(5, 30)},
]