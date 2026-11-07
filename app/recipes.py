"""Recipes: a workflow in API format plus a map from friendly inputs to node fields.

A recipe folder under ``workflows/`` holds ``recipe.json``, the API-format
graph it names, and a README with model provenance. The app never edits the
graph structure; it only writes values into the fields the recipe declares.
"""

from __future__ import annotations

import copy
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class RecipeError(ValueError):
    pass


@dataclass
class InputSpec:
    name: str
    node: str
    field: str
    type: str  # string | int | float | choice | image | seed
    required: bool = False
    default: Any = None
    label: str = ""
    help: str = ""
    choices: list[str] = field(default_factory=list)
    min: float | None = None
    max: float | None = None
    step: float | None = None

    def to_public(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "default": self.default,
            "label": self.label or self.name,
            "help": self.help,
            "choices": self.choices,
            "min": self.min,
            "max": self.max,
            "step": self.step,
        }


@dataclass
class Recipe:
    name: str
    title: str
    kind: str
    description: str
    folder: Path
    graph: dict
    inputs: dict[str, InputSpec]
    output_node: str | None = None

    def to_public(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "kind": self.kind,
            "description": self.description,
            "inputs": [spec.to_public() for spec in self.inputs.values()],
        }

    def build(self, values: dict[str, Any]) -> tuple[dict, dict]:
        """Return ``(graph, resolved_values)`` with the inputs written in."""
        graph = copy.deepcopy(self.graph)
        resolved: dict[str, Any] = {}
        for name, spec in self.inputs.items():
            raw = values.get(name)
            if raw is None or raw == "":
                if spec.required:
                    raise RecipeError(f"'{spec.label or name}' is required")
                raw = spec.default
            value = _coerce(spec, raw)
            node = graph.get(spec.node)
            if node is None or "inputs" not in node:
                raise RecipeError(f"recipe '{self.name}' names node {spec.node}, which the graph does not have")
            node["inputs"][spec.field] = value
            resolved[name] = value
        unknown = set(values) - set(self.inputs)
        if unknown:
            raise RecipeError(f"unknown inputs for '{self.name}': {', '.join(sorted(unknown))}")
        return graph, resolved


def _coerce(spec: InputSpec, raw: Any) -> Any:
    t = spec.type
    if t == "seed":
        if raw in (None, "", "random", -1, "-1"):
            return random.randint(0, 2**53)
        return int(raw)
    if t == "int":
        value = int(float(raw))
    elif t == "float":
        value = float(raw)
    elif t == "choice":
        value = str(raw)
        if spec.choices and value not in spec.choices:
            raise RecipeError(f"'{spec.label or spec.name}' must be one of: {', '.join(spec.choices)}")
        return value
    elif t in ("string", "image"):
        value = str(raw)
        if t == "image" and not value:
            raise RecipeError(f"'{spec.label or spec.name}' needs an uploaded image")
        return value
    else:
        raise RecipeError(f"unknown input type '{t}' in recipe")
    if spec.min is not None and value < spec.min:
        raise RecipeError(f"'{spec.label or spec.name}' must be at least {spec.min}")
    if spec.max is not None and value > spec.max:
        raise RecipeError(f"'{spec.label or spec.name}' must be at most {spec.max}")
    return value


def load_recipes(workflows_dir: Path) -> dict[str, Recipe]:
    recipes: dict[str, Recipe] = {}
    for recipe_file in sorted(workflows_dir.glob("*/recipe.json")):
        folder = recipe_file.parent
        meta = json.loads(recipe_file.read_text(encoding="utf-8"))
        graph_path = folder / meta.get("workflow", "workflow.api.json")
        if not graph_path.is_file():
            raise RecipeError(f"{recipe_file}: workflow file {graph_path.name} is missing")
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        inputs: dict[str, InputSpec] = {}
        for name, spec in (meta.get("inputs") or {}).items():
            inputs[name] = InputSpec(
                name=name,
                node=str(spec["node"]),
                field=spec["field"],
                type=spec.get("type", "string"),
                required=bool(spec.get("required", False)),
                default=spec.get("default"),
                label=spec.get("label", ""),
                help=spec.get("help", ""),
                choices=list(spec.get("choices") or []),
                min=spec.get("min"),
                max=spec.get("max"),
                step=spec.get("step"),
            )
            if inputs[name].node not in graph:
                raise RecipeError(f"{recipe_file}: input '{name}' points at node {spec['node']}, not in the graph")
        name = meta.get("name") or folder.name
        recipes[name] = Recipe(
            name=name,
            title=meta.get("title", name),
            kind=meta.get("kind", "video"),
            description=meta.get("description", ""),
            folder=folder,
            graph=graph,
            inputs=inputs,
            output_node=meta.get("output_node"),
        )
    return recipes
