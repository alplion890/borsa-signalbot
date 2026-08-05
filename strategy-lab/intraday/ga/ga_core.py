"""Generic genetik algoritma motoru (bagimsiz, numpy).

Strateji bilgisi YOK. Param uzayi + fitness fonksiyonu disaridan verilir.

Param uzayi (Gene):
    GeneFloat("rr", 0.5, 3.0)            -> surekli
    GeneInt("max_hold", 12, 96)          -> tam sayi
    GeneChoice("trend", ["none","ema"])  -> kategorik

Kullanim:
    space = [GeneFloat("rr", 0.5, 3.0), GeneChoice("trend", ["ema","vwap"])]
    best, hist = run_ga(space, fitness_fn, pop=20, generations=15, seed=7)
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class GeneFloat:
    name: str
    lo: float
    hi: float

    def sample(self, rng: random.Random) -> float:
        return rng.uniform(self.lo, self.hi)

    def mutate(self, val, rng: random.Random):
        span = (self.hi - self.lo) * 0.2
        return float(np.clip(val + rng.gauss(0, span), self.lo, self.hi))


@dataclass(frozen=True)
class GeneInt:
    name: str
    lo: int
    hi: int

    def sample(self, rng: random.Random) -> int:
        return rng.randint(self.lo, self.hi)

    def mutate(self, val, rng: random.Random):
        span = max(1, int((self.hi - self.lo) * 0.2))
        return int(np.clip(val + rng.randint(-span, span), self.lo, self.hi))


@dataclass(frozen=True)
class GeneChoice:
    name: str
    options: tuple

    def __init__(self, name: str, options):
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "options", tuple(options))

    def sample(self, rng: random.Random):
        return rng.choice(self.options)

    def mutate(self, val, rng: random.Random):
        return rng.choice(self.options)


Gene = GeneFloat | GeneInt | GeneChoice
Genome = dict
FitnessFn = Callable[[Genome], float]


def _random_genome(space: list[Gene], rng: random.Random) -> Genome:
    return {g.name: g.sample(rng) for g in space}


def _crossover(a: Genome, b: Genome, space: list[Gene], rng: random.Random) -> Genome:
    return {g.name: (a if rng.random() < 0.5 else b)[g.name] for g in space}


def _mutate(genome: Genome, space: list[Gene], rate: float, rng: random.Random) -> Genome:
    out = dict(genome)
    for g in space:
        if rng.random() < rate:
            out[g.name] = g.mutate(out[g.name], rng)
    return out


def _tournament(pop, fits, k, rng: random.Random):
    idx = rng.sample(range(len(pop)), min(k, len(pop)))
    best = max(idx, key=lambda i: fits[i])
    return pop[best]


def run_ga(
    space: list[Gene],
    fitness_fn: FitnessFn,
    pop: int = 20,
    generations: int = 15,
    elite: int = 2,
    mutation_rate: float = 0.25,
    tournament_k: int = 3,
    seed: int = 7,
    on_eval: Callable[[Genome, float], None] | None = None,
    verbose: bool = True,
):
    """GA calistir. (best_genome, best_fitness, history) dondurur.

    fitness_fn yuksek=iyi. NaN/inf fitness -inf'e cevrilir.
    on_eval her degerlendirme sonrasi cagrilir (gate-gecen adaylari toplamak icin).
    """
    rng = random.Random(seed)
    cache: dict[tuple, float] = {}

    def evaluate(genome: Genome) -> float:
        key = tuple(sorted((k, round(v, 6) if isinstance(v, float) else v)
                           for k, v in genome.items()))
        if key in cache:
            return cache[key]
        try:
            f = float(fitness_fn(genome))
        except Exception:
            f = float("-inf")
        if not np.isfinite(f):
            f = float("-inf")
        cache[key] = f
        if on_eval is not None:
            on_eval(genome, f)
        return f

    population = [_random_genome(space, rng) for _ in range(pop)]
    fits = [evaluate(g) for g in population]
    history = []
    best_i = int(np.argmax(fits))
    best, best_f = dict(population[best_i]), fits[best_i]

    for gen in range(generations):
        order = sorted(range(len(population)), key=lambda i: fits[i], reverse=True)
        new_pop = [dict(population[i]) for i in order[:elite]]
        while len(new_pop) < pop:
            p1 = _tournament(population, fits, tournament_k, rng)
            p2 = _tournament(population, fits, tournament_k, rng)
            child = _crossover(p1, p2, space, rng)
            child = _mutate(child, space, mutation_rate, rng)
            new_pop.append(child)
        population = new_pop
        fits = [evaluate(g) for g in population]
        gi = int(np.argmax(fits))
        if fits[gi] > best_f:
            best, best_f = dict(population[gi]), fits[gi]
        history.append({"gen": gen, "best": best_f, "mean": float(np.mean(
            [f for f in fits if np.isfinite(f)] or [float("nan")]))})
        if verbose:
            print(f"    gen {gen:2d}  best={best_f:8.3f}  mean={history[-1]['mean']:8.3f}  "
                  f"evals={len(cache)}")
    return best, best_f, history
