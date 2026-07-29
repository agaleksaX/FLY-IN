#!/usr/bin/env python3
"""Entry point for the Fly-In drone simulation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from parser.tokenizer import Tokenizer
from parser.parser import Parser
from parser.validator import Validator
from simulation.engine import Engine
from visualization.terminal import (
    print_simulation_header,
    print_turn,
    print_simulation_summary,
)


def main(argv: list[str] | None = None) -> int:
    """Run the drone simulation from a map file."""
    parser = argparse.ArgumentParser(
        description="Fly-In Drone Routing Simulation",
    )
    parser.add_argument(
        "map_file",
        help="Path to the map file",
    )
    parser.add_argument(
        "--visual",
        "-v",
        action="store_true",
        help="Show matplotlib animated visualization after simulation",
    )
    parser.add_argument(
        "--snapshot",
        "-s",
        action="store_true",
        help="Show a matplotlib snapshot after each turn (implies --visual)",
    )
    args = parser.parse_args(argv)
    
    map_path = Path(args.map_file)
    if not map_path.exists():
        print(f"Error: File '{map_path}' not found".)
        return 1
    
    try:
        text = map_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Error reading file: {exc}")
        return 1
    
    tokenizer = Tokenizer()
    tokens = tokenizer.tokenize(text)
    
    validator = Validator()
    validator.validate(tokens)
    
    parser_obj = Parser()
    config = parser_obj.parse(tokens)
    
    engine = Engine(config)
    print_simulation_header(config)
    turns = engine.run()
    
    for i, turn in enumerate(turns, start=1):
        print_turn(i, turn, config.graph)
        
    print_simulation_summary(len(turns), config)
    
    if args.visual or args.snapshot:
        try:
            import matplotlib.pyplot as plt
            from visualization.matplotlib_viz import (
                animate_simulation,
                draw_turn_snapshot,
            )
        except ImportError:
            print(
                "Warning: matplotlib not innstalled. "
                "Install with: piop install matplotlib"
            )
            return 0
        
        plt.close("all")
        
        if args.snapshot:
            for i, turn in enumerate(turns, start=1):
                draw_turn_snapshot(config.graph, turns, config)
        
        elif args.visual:
            animate_simulation(config.graph, turns, config)
            
    return 0


if __name__ == "__main__":
    sys.exit(main())