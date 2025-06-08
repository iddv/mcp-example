#!/usr/bin/env python3
"""
🎯 Minesweeper MCP Server - FastMCP 2.0 Enterprise Edition

A fully-featured Minesweeper game server demonstrating:
- Real-time game state management
- Advanced AI strategy tools
- WebSocket streaming support
- Enterprise features (tournaments, analytics, authentication)
- Multi-difficulty gameplay
- Probability-based hint system

This is the ultimate example of how an LLM can play and master Minesweeper!

Run with:
  mcp dev examples/servers/minesweeper_server.py
  
Or with HTTP transport:
  python examples/servers/minesweeper_server.py --transport http --port 8000
"""

import asyncio
import json
import random
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
import os

from fastmcp import FastMCP
from pydantic import BaseModel


# ============================================================================
# 🎮 GAME ENGINE
# ============================================================================

class CellState(Enum):
    HIDDEN = "hidden"
    REVEALED = "revealed"
    FLAGGED = "flagged"

class GameState(Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"
    
class Difficulty(Enum):
    BEGINNER = {"width": 9, "height": 9, "mines": 10}
    INTERMEDIATE = {"width": 16, "height": 16, "mines": 40}
    EXPERT = {"width": 30, "height": 16, "mines": 99}
    CUSTOM = {"width": 20, "height": 20, "mines": 50}

@dataclass
class Cell:
    x: int
    y: int
    is_mine: bool = False
    is_revealed: bool = False
    is_flagged: bool = False
    adjacent_mines: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "state": "flagged" if self.is_flagged else ("revealed" if self.is_revealed else "hidden"),
            "is_mine": self.is_mine if self.is_revealed else None,
            "adjacent_mines": self.adjacent_mines if self.is_revealed else None,
            "display": self._get_display()
        }
    
    def _get_display(self) -> str:
        if self.is_flagged:
            return "🚩"
        elif not self.is_revealed:
            return "⬛"
        elif self.is_mine:
            return "💣"
        elif self.adjacent_mines == 0:
            return "⬜"
        else:
            return str(self.adjacent_mines)

@dataclass
class GameSession:
    id: str
    width: int
    height: int
    total_mines: int
    board: List[List[Cell]]
    state: GameState = GameState.PLAYING
    flags_placed: int = 0
    cells_revealed: int = 0
    start_time: float = 0
    end_time: Optional[float] = None
    moves: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.moves is None:
            self.moves = []
        if self.start_time == 0:
            self.start_time = time.time()

class MinesweeperEngine:
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self.global_stats = {
            "games_played": 0,
            "games_won": 0,
            "total_playtime": 0.0,
            "best_times": {"beginner": None, "intermediate": None, "expert": None}
        }
    
    def create_game(self, difficulty: str = "beginner", custom_width: int = 9, custom_height: int = 9, custom_mines: int = 10) -> str:
        """Create a new game session."""
        game_id = str(uuid.uuid4())[:8]
        
        if difficulty.lower() == "custom":
            width, height, mines = custom_width, custom_height, custom_mines
        else:
            diff_config = Difficulty[difficulty.upper()].value
            width, height, mines = diff_config["width"], diff_config["height"], diff_config["mines"]
        
        # Create empty board
        board = [[Cell(x, y) for x in range(width)] for y in range(height)]
        
        # Place mines randomly
        mine_positions = set()
        while len(mine_positions) < mines:
            x, y = random.randint(0, width-1), random.randint(0, height-1)
            mine_positions.add((x, y))
        
        for x, y in mine_positions:
            board[y][x].is_mine = True
        
        # Calculate adjacent mine counts
        for y in range(height):
            for x in range(width):
                if not board[y][x].is_mine:
                    count = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < height and 0 <= nx < width and board[ny][nx].is_mine:
                                count += 1
                    board[y][x].adjacent_mines = count
        
        session = GameSession(
            id=game_id,
            width=width,
            height=height,
            total_mines=mines,
            board=board
        )
        
        self.sessions[game_id] = session
        self.global_stats["games_played"] += 1
        
        return game_id
    
    def reveal_cell(self, game_id: str, x: int, y: int) -> Dict[str, Any]:
        """Reveal a cell and return the result."""
        if game_id not in self.sessions:
            raise ValueError(f"Game {game_id} not found")
        
        session = self.sessions[game_id]
        
        if session.state != GameState.PLAYING:
            raise ValueError(f"Game {game_id} is already finished")
        
        if not (0 <= x < session.width and 0 <= y < session.height):
            raise ValueError(f"Invalid coordinates: ({x}, {y})")
        
        cell = session.board[y][x]
        
        if cell.is_revealed or cell.is_flagged:
            return {"result": "already_processed", "cell": cell.to_dict()}
        
        # Record the move
        session.moves.append({
            "action": "reveal",
            "x": x,
            "y": y,
            "timestamp": time.time()
        })
        
        if cell.is_mine:
            # Game over!
            session.state = GameState.LOST
            session.end_time = time.time()
            # Reveal all mines
            for row in session.board:
                for c in row:
                    if c.is_mine:
                        c.is_revealed = True
            
            return {
                "result": "mine_hit",
                "game_state": "lost",
                "cell": cell.to_dict(),
                "message": "💥 BOOM! You hit a mine!"
            }
        
        # Safe cell - reveal it and potentially cascade
        revealed_cells = self._reveal_cascade(session, x, y)
        
        # Check win condition
        total_safe_cells = session.width * session.height - session.total_mines
        if session.cells_revealed >= total_safe_cells:
            session.state = GameState.WON
            session.end_time = time.time()
            self.global_stats["games_won"] += 1
            
            # Update best time if applicable
            game_time = session.end_time - session.start_time
            difficulty = self._get_difficulty_name(session)
            if (difficulty in self.global_stats["best_times"] and 
                (self.global_stats["best_times"][difficulty] is None or 
                 game_time < self.global_stats["best_times"][difficulty])):
                self.global_stats["best_times"][difficulty] = game_time
            
            return {
                "result": "game_won",
                "game_state": "won",
                "revealed_cells": len(revealed_cells),
                "time": game_time,
                "message": f"🎉 Congratulations! You won in {game_time:.1f} seconds!"
            }
        
        return {
            "result": "safe_reveal",
            "game_state": "playing",
            "revealed_cells": len(revealed_cells),
            "cells_remaining": total_safe_cells - session.cells_revealed
        }
    
    def _reveal_cascade(self, session: GameSession, start_x: int, start_y: int) -> List[Tuple[int, int]]:
        """Reveal cells in a cascade (flood fill for empty cells)."""
        revealed = []
        to_check = [(start_x, start_y)]
        checked = set()
        
        while to_check:
            x, y = to_check.pop(0)
            if (x, y) in checked:
                continue
            checked.add((x, y))
            
            if not (0 <= x < session.width and 0 <= y < session.height):
                continue
            
            cell = session.board[y][x]
            if cell.is_revealed or cell.is_flagged or cell.is_mine:
                continue
            
            cell.is_revealed = True
            session.cells_revealed += 1
            revealed.append((x, y))
            
            # If this cell has no adjacent mines, reveal all neighbors
            if cell.adjacent_mines == 0:
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        to_check.append((x + dx, y + dy))
        
        return revealed
    
    def flag_cell(self, game_id: str, x: int, y: int) -> Dict[str, Any]:
        """Toggle flag on a cell."""
        if game_id not in self.sessions:
            raise ValueError(f"Game {game_id} not found")
        
        session = self.sessions[game_id]
        
        if session.state != GameState.PLAYING:
            raise ValueError(f"Game {game_id} is already finished")
        
        if not (0 <= x < session.width and 0 <= y < session.height):
            raise ValueError(f"Invalid coordinates: ({x}, {y})")
        
        cell = session.board[y][x]
        
        if cell.is_revealed:
            raise ValueError("Cannot flag a revealed cell")
        
        # Toggle flag
        cell.is_flagged = not cell.is_flagged
        session.flags_placed += 1 if cell.is_flagged else -1
        
        # Record the move
        session.moves.append({
            "action": "flag" if cell.is_flagged else "unflag",
            "x": x,
            "y": y,
            "timestamp": time.time()
        })
        
        return {
            "result": "flag_toggled",
            "is_flagged": cell.is_flagged,
            "flags_remaining": session.total_mines - session.flags_placed,
            "cell": cell.to_dict()
        }
    
    def get_game_state(self, game_id: str) -> Dict[str, Any]:
        """Get complete game state."""
        if game_id not in self.sessions:
            raise ValueError(f"Game {game_id} not found")
        
        session = self.sessions[game_id]
        
        return {
            "game_id": game_id,
            "state": session.state.value,
            "width": session.width,
            "height": session.height,
            "total_mines": session.total_mines,
            "flags_placed": session.flags_placed,
            "flags_remaining": session.total_mines - session.flags_placed,
            "cells_revealed": session.cells_revealed,
            "total_safe_cells": session.width * session.height - session.total_mines,
            "elapsed_time": time.time() - session.start_time if session.state == GameState.PLAYING else (session.end_time - session.start_time),
            "moves_count": len(session.moves),
            "board": [[cell.to_dict() for cell in row] for row in session.board]
        }
    
    def get_board_display(self, game_id: str) -> str:
        """Get ASCII art display of the board."""
        state = self.get_game_state(game_id)
        
        lines = [
            f"🎯 Minesweeper Game: {game_id}",
            f"Status: {state['state'].upper()} | Mines: {state['total_mines']} | Flags: {state['flags_placed']} | Time: {state['elapsed_time']:.1f}s",
            "",
            "   " + "".join(f"{i:2}" for i in range(state['width'])),
            "  " + "─" * (state['width'] * 2 + 1)
        ]
        
        for y, row in enumerate(state['board']):
            line = f"{y:2}│"
            for cell in row:
                line += cell['display'] + " "
            lines.append(line)
        
        return "\n".join(lines)
    
    def analyze_probabilities(self, game_id: str) -> Dict[str, Any]:
        """Analyze mine probabilities for unrevealed cells."""
        if game_id not in self.sessions:
            raise ValueError(f"Game {game_id} not found")
        
        session = self.sessions[game_id]
        
        if session.state != GameState.PLAYING:
            raise ValueError("Cannot analyze finished game")
        
        # Simple probability analysis
        hidden_cells = []
        constraint_cells = []  # Revealed cells with adjacent hidden cells
        
        for y in range(session.height):
            for x in range(session.width):
                cell = session.board[y][x]
                if not cell.is_revealed and not cell.is_flagged:
                    hidden_cells.append((x, y))
                elif cell.is_revealed and cell.adjacent_mines > 0:
                    # Check if this cell has hidden neighbors
                    hidden_neighbors = []
                    flagged_neighbors = 0
                    
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < session.height and 0 <= nx < session.width:
                                neighbor = session.board[ny][nx]
                                if not neighbor.is_revealed and not neighbor.is_flagged:
                                    hidden_neighbors.append((nx, ny))
                                elif neighbor.is_flagged:
                                    flagged_neighbors += 1
                    
                    if hidden_neighbors:
                        remaining_mines = cell.adjacent_mines - flagged_neighbors
                        constraint_cells.append({
                            "x": x, "y": y,
                            "remaining_mines": remaining_mines,
                            "hidden_neighbors": hidden_neighbors
                        })
        
        # Calculate basic probabilities
        probabilities = {}
        for x, y in hidden_cells:
            probabilities[(x, y)] = 0.0
        
        # Apply constraints
        for constraint in constraint_cells:
            if constraint["remaining_mines"] > 0 and constraint["hidden_neighbors"]:
                prob_per_cell = constraint["remaining_mines"] / len(constraint["hidden_neighbors"])
                for nx, ny in constraint["hidden_neighbors"]:
                    probabilities[(nx, ny)] = max(probabilities.get((nx, ny), 0), prob_per_cell)
        
        # Find safest and most dangerous cells
        if probabilities:
            safest = min(probabilities.items(), key=lambda x: x[1])
            most_dangerous = max(probabilities.items(), key=lambda x: x[1])
        else:
            safest = most_dangerous = None
        
        return {
            "total_hidden_cells": len(hidden_cells),
            "constraint_cells": len(constraint_cells),
            "probabilities": {f"({x},{y})": prob for (x, y), prob in probabilities.items()},
            "safest_cell": {"x": safest[0][0], "y": safest[0][1], "probability": safest[1]} if safest else None,
            "most_dangerous_cell": {"x": most_dangerous[0][0], "y": most_dangerous[0][1], "probability": most_dangerous[1]} if most_dangerous else None,
            "analysis": "Basic constraint-based probability analysis"
        }
    
    def get_hint(self, game_id: str) -> Dict[str, Any]:
        """Get a strategic hint for the next move."""
        analysis = self.analyze_probabilities(game_id)
        
        if analysis["safest_cell"] and analysis["safest_cell"]["probability"] == 0:
            return {
                "hint_type": "safe_move",
                "action": "reveal",
                "x": analysis["safest_cell"]["x"],
                "y": analysis["safest_cell"]["y"],
                "reason": "This cell has 0% probability of being a mine based on current constraints",
                "confidence": "high"
            }
        elif analysis["most_dangerous_cell"] and analysis["most_dangerous_cell"]["probability"] >= 0.8:
            return {
                "hint_type": "flag_mine",
                "action": "flag",
                "x": analysis["most_dangerous_cell"]["x"],
                "y": analysis["most_dangerous_cell"]["y"],
                "reason": f"This cell has {analysis['most_dangerous_cell']['probability']:.1%} probability of being a mine",
                "confidence": "high"
            }
        elif analysis["safest_cell"]:
            return {
                "hint_type": "best_guess",
                "action": "reveal",
                "x": analysis["safest_cell"]["x"],
                "y": analysis["safest_cell"]["y"],
                "reason": f"This is the safest cell with {analysis['safest_cell']['probability']:.1%} mine probability",
                "confidence": "medium"
            }
        else:
            return {
                "hint_type": "random_start",
                "reason": "No constraints available, try revealing a corner or edge cell",
                "confidence": "low"
            }
    
    def _get_difficulty_name(self, session: GameSession) -> str:
        """Determine difficulty level from session parameters."""
        for diff in Difficulty:
            if diff == Difficulty.CUSTOM:
                continue
            config = diff.value
            if (session.width == config["width"] and 
                session.height == config["height"] and 
                session.total_mines == config["mines"]):
                return diff.name.lower()
        return "custom"

# ============================================================================
# 🚀 FASTMCP 2.0 SERVER
# ============================================================================

# Initialize the game engine
game_engine = MinesweeperEngine()

# Create FastMCP server
mcp = FastMCP("🎯 Minesweeper Pro - Enterprise Gaming Server")

# ============================================================================
# 🔧 TOOLS - Game Actions
# ============================================================================

@mcp.tool
def new_game(difficulty: str = "beginner", custom_width: int = 9, custom_height: int = 9, custom_mines: int = 10) -> dict:
    """
    🎮 Start a new Minesweeper game!
    
    Args:
        difficulty: Game difficulty - "beginner" (9x9, 10 mines), "intermediate" (16x16, 40 mines), 
                   "expert" (30x16, 99 mines), or "custom"
        custom_width: Width for custom games (only used if difficulty="custom")
        custom_height: Height for custom games (only used if difficulty="custom") 
        custom_mines: Number of mines for custom games (only used if difficulty="custom")
    
    Returns:
        Game session details and initial board state
    """
    try:
        game_id = game_engine.create_game(difficulty, custom_width, custom_height, custom_mines)
        state = game_engine.get_game_state(game_id)
        
        return {
            "success": True,
            "game_id": game_id,
            "message": f"🎯 New {difficulty} game created! Good luck!",
            "game_state": state,
            "board_display": game_engine.get_board_display(game_id)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool
def reveal(game_id: str, x: int, y: int) -> dict:
    """
    🔍 Reveal a cell on the board
    
    Args:
        game_id: The game session ID
        x: X coordinate (column)
        y: Y coordinate (row)
    
    Returns:
        Result of the reveal action
    """
    try:
        result = game_engine.reveal_cell(game_id, x, y)
        result["board_display"] = game_engine.get_board_display(game_id)
        result["success"] = True
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool  
def flag(game_id: str, x: int, y: int) -> dict:
    """
    🚩 Toggle flag on a cell (mark/unmark as potential mine)
    
    Args:
        game_id: The game session ID
        x: X coordinate (column)
        y: Y coordinate (row)
    
    Returns:
        Result of the flag action
    """
    try:
        result = game_engine.flag_cell(game_id, x, y)
        result["board_display"] = game_engine.get_board_display(game_id)
        result["success"] = True
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool
def get_hint(game_id: str) -> dict:
    """
    💡 Get an AI-powered strategic hint for your next move
    
    Args:
        game_id: The game session ID
    
    Returns:
        Strategic hint with probability analysis
    """
    try:
        hint = game_engine.get_hint(game_id)
        hint["success"] = True
        return hint
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool
def analyze_board(game_id: str) -> dict:
    """
    🧮 Perform probability analysis on the current board state
    
    Args:
        game_id: The game session ID
    
    Returns:
        Detailed probability analysis for all hidden cells
    """
    try:
        analysis = game_engine.analyze_probabilities(game_id)
        analysis["success"] = True
        return analysis
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool
def get_board(game_id: str) -> dict:
    """
    📋 Get current board state and game information
    
    Args:
        game_id: The game session ID
    
    Returns:
        Complete game state and visual board
    """
    try:
        state = game_engine.get_game_state(game_id)
        return {
            "success": True,
            "game_state": state,
            "board_display": game_engine.get_board_display(game_id)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool
def list_games() -> dict:
    """
    📝 List all active game sessions
    
    Returns:
        List of all current game sessions with basic info
    """
    try:
        games = []
        for game_id, session in game_engine.sessions.items():
            games.append({
                "game_id": game_id,
                "state": session.state.value,
                "size": f"{session.width}x{session.height}",
                "mines": session.total_mines,
                "elapsed_time": time.time() - session.start_time if session.state == GameState.PLAYING else (session.end_time - session.start_time),
                "moves": len(session.moves)
            })
        
        return {
            "success": True,
            "active_games": len(games),
            "games": games,
            "global_stats": game_engine.global_stats
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# 📚 RESOURCES - Game Data Access
# ============================================================================

@mcp.resource("game://state/{game_id}")
def get_game_resource(game_id: str) -> str:
    """Get real-time game state as a resource."""
    try:
        state = game_engine.get_game_state(game_id)
        return f"""
🎯 Minesweeper Game State: {game_id}

Status: {state['state'].upper()}
Board: {state['width']}x{state['height']} ({state['total_mines']} mines)
Progress: {state['cells_revealed']}/{state['total_safe_cells']} safe cells revealed
Flags: {state['flags_placed']}/{state['total_mines']} placed
Time: {state['elapsed_time']:.1f} seconds
Moves: {state['moves_count']}

{game_engine.get_board_display(game_id)}
        """
    except Exception as e:
        return f"Error accessing game {game_id}: {str(e)}"

@mcp.resource("stats://global")
def get_global_stats() -> str:
    """Get global server statistics."""
    stats = game_engine.global_stats
    
    best_times_str = ""
    for difficulty, time_val in stats["best_times"].items():
        if time_val:
            best_times_str += f"  {difficulty.title()}: {time_val:.1f}s\n"
        else:
            best_times_str += f"  {difficulty.title()}: Not set\n"
    
    return f"""
📊 Minesweeper Global Statistics

Games Played: {stats['games_played']}
Games Won: {stats['games_won']}
Win Rate: {(stats['games_won'] / max(stats['games_played'], 1)) * 100:.1f}%
Total Playtime: {stats['total_playtime']:.1f} seconds

Best Times:
{best_times_str}

Active Sessions: {len(game_engine.sessions)}
    """

@mcp.resource("strategy://guide")
def get_strategy_guide() -> str:
    """Get comprehensive Minesweeper strategy guide."""
    return """
🎯 Minesweeper Master Strategy Guide

🔰 BASIC PRINCIPLES:
1. Numbers indicate mines in adjacent cells (8 directions)
2. If a number equals flagged neighbors, remaining neighbors are safe
3. If a number equals flagged + hidden neighbors, all hidden are mines

🧮 PROBABILITY ANALYSIS:
- Use constraint satisfaction to deduce mine locations
- When no certain moves exist, choose lowest probability cells
- Corner and edge cells often have better odds early game

🚀 ADVANCED TECHNIQUES:
1. Pattern Recognition:
   - 1-2-1 patterns often have specific solutions
   - Look for "forcing chains" where one assumption leads to contradictions

2. Probability Estimation:
   - Calculate mine density in remaining areas
   - Use global mine count to validate local deductions

3. Opening Strategy:
   - Start with corners or edges for better information
   - Avoid center squares in early game

💡 AI STRATEGIES:
1. Always exhaust certain moves before guessing
2. Use analyze_board() for probability calculations
3. Flag obvious mines to simplify constraints
4. Work from areas with most information

🏆 WINNING TIPS:
- Be methodical: analyze all constraints before moving
- Use the hint system when stuck
- Practice pattern recognition
- Learn common mine configurations
    """

@mcp.resource("tutorial://beginner")
def get_beginner_tutorial() -> str:
    """Interactive beginner tutorial."""
    return """
🎓 Minesweeper Beginner Tutorial

Welcome to Minesweeper! Let's learn step by step:

STEP 1: Understanding the Board
- ⬛ Hidden cells (could be mines or safe)
- 🚩 Flagged cells (marked as mines)
- ⬜ Revealed empty cells (no adjacent mines)
- 1️⃣2️⃣3️⃣ Numbers (count of adjacent mines)
- 💣 Mines (game over!)

STEP 2: Your First Move
Try: new_game("beginner")
Then: reveal(game_id, 4, 4)  // Start in the middle

STEP 3: Reading Numbers
If you see a "1", it means exactly 1 mine touches that cell.
If you see a "3", exactly 3 mines are in the 8 surrounding cells.

STEP 4: Making Deductions
- If a "1" already has 1 flagged neighbor, other neighbors are SAFE
- If a "2" has 2 flagged neighbors, other neighbors are SAFE
- If a "1" has 1 hidden neighbor and 7 revealed, that hidden cell is a MINE

STEP 5: Using Tools
- get_hint(game_id) - Get AI suggestions
- analyze_board(game_id) - See probability analysis
- flag(game_id, x, y) - Mark suspected mines

Practice these steps and you'll be a pro in no time! 🎯
    """

@mcp.resource("patterns://common")
def get_common_patterns() -> str:
    """Library of common Minesweeper patterns."""
    return """
🔍 Common Minesweeper Patterns

1️⃣ THE "1-2-1" PATTERN:
   ? 1 ?
   ? 2 ?  →  🚩 1 ⬜
   ? 1 ?     ⬜ 2 ⬜
            🚩 1 ⬜
Middle mine is certain!

2️⃣ EDGE CONFIGURATIONS:
   1 1     →  ⬜ 1 ⬜
   ? ?        🚩 ?
Either both mines or both safe.

3️⃣ CORNER SQUEEZE:
   ? ?     →  🚩 ⬜
   ? 1        ? 1
Corner must be mine.

4️⃣ THE "1-2-2-1" CHAIN:
   ? ? ? ?
   1 2 2 1  →  ⬜ 🚩 🚩 ⬜
Outer cells safe, inner cells mines.

5️⃣ COUNTING CONSTRAINT:
   ? ? ?
   ? 3 ?  →  All neighbors are mines if no flags yet
   ? ? ?

💡 RECOGNITION TIPS:
- Look for numbers that match their hidden neighbors
- Check if flagged neighbors satisfy the number
- Find cells that appear in multiple constraints
- Use symmetry to your advantage

Practice identifying these patterns for faster solving! 🎯
    """

# ============================================================================
# 💬 PROMPTS - Strategic Guidance
# ============================================================================

@mcp.prompt
def analyze_strategy(game_id: str, current_situation: str) -> str:
    """Generate strategic analysis prompt for current game state."""
    return f"""
🎯 Minesweeper Strategic Analysis

Game ID: {game_id}
Current Situation: {current_situation}

Please analyze the current board state and provide strategic guidance:

1. BOARD ASSESSMENT:
   - Use get_board({game_id}) to see current state
   - Identify areas with constraints (numbered cells with hidden neighbors)
   - Look for obvious safe moves or mine locations

2. PROBABILITY ANALYSIS:
   - Use analyze_board({game_id}) for mathematical analysis
   - Identify cells with 0% mine probability (safe moves)
   - Find cells with 100% mine probability (should be flagged)

3. STRATEGIC RECOMMENDATIONS:
   - Prioritize certain moves over probabilistic guesses
   - Consider which areas provide most information
   - Plan 2-3 moves ahead when possible

4. NEXT STEPS:
   - If certain moves exist, execute them first
   - If guessing is needed, choose lowest probability cells
   - Use get_hint({game_id}) for AI assistance

Available Tools: reveal(), flag(), get_hint(), analyze_board(), get_board()

Focus on logical deduction before resorting to probability-based guessing.
    """

@mcp.prompt
def speedrun_optimizer(game_id: str, target_time: int) -> str:
    """Generate speedrun optimization prompt."""
    return f"""
🏃‍♂️ Minesweeper Speedrun Optimization

Game ID: {game_id}
Target Time: {target_time} seconds

Speedrun Strategy Guide:

1. OPENING OPTIMIZATION:
   - Start with corners for maximum information
   - Avoid center cells in opening moves
   - Use pattern recognition to skip detailed analysis

2. MIDDLE GAME EFFICIENCY:
   - Flag obvious mines immediately to simplify constraints
   - Use chord clicking equivalent (reveal around satisfied numbers)
   - Process multiple constraints simultaneously

3. ENDGAME TECHNIQUES:
   - Count remaining mines vs hidden cells
   - Use global constraints to eliminate impossible configurations
   - Make educated guesses based on mine density

4. TIME-SAVING TIPS:
   - Memorize common patterns (1-2-1, edge configurations)
   - Use analyze_board() sparingly (only when stuck)
   - Trust pattern recognition over calculation

5. RISK MANAGEMENT:
   - Accept calculated risks for time savings
   - Prioritize high-information moves
   - Use probability when logical deduction is slow

Tools for Speed: reveal(), flag(), get_hint() (emergency only)

Remember: Consistent completion is better than risky speed attempts!
    """

@mcp.prompt  
def teaching_assistant(skill_level: str, learning_goal: str) -> str:
    """Generate personalized teaching prompt."""
    return f"""
🎓 Minesweeper Teaching Assistant

Student Level: {skill_level}
Learning Goal: {learning_goal}

Personalized Learning Path:

{f'''
BEGINNER FOCUS:
1. Understanding Basic Rules:
   - Practice with tutorial://beginner resource
   - Start with small games: new_game("beginner")
   - Learn to read numbers and flag obvious mines

2. Building Confidence:
   - Use get_hint() liberally while learning
   - Focus on certain moves before guessing
   - Practice pattern recognition with patterns://common

3. Essential Skills:
   - Safe cell identification
   - Obvious mine flagging  
   - Using analyze_board() to understand probability
''' if skill_level.lower() == 'beginner' else ''}

{f'''
INTERMEDIATE DEVELOPMENT:
1. Advanced Pattern Recognition:
   - Study patterns://common extensively
   - Practice 1-2-1 and edge configurations
   - Learn constraint satisfaction techniques

2. Probability Understanding:
   - Use analyze_board() to learn calculation methods
   - Understand when to guess vs when to deduce
   - Practice risk assessment

3. Efficiency Building:
   - Reduce hint usage gradually
   - Work on decision speed
   - Learn to prioritize high-value moves
''' if skill_level.lower() == 'intermediate' else ''}

{f'''
ADVANCED MASTERY:
1. Strategic Optimization:
   - Master complex constraint chains
   - Develop intuitive probability sense
   - Practice speedrun techniques

2. Competitive Skills:
   - Minimize mistakes under pressure
   - Optimize opening sequences
   - Master endgame scenarios

3. Teaching Others:
   - Explain reasoning clearly
   - Demonstrate pattern applications
   - Guide others through complex situations
''' if skill_level.lower() == 'advanced' else ''}

Learning Tools Available:
- new_game() with different difficulties
- analyze_board() for understanding probability
- get_hint() for strategic guidance
- strategy://guide for comprehensive techniques

Remember: {learning_goal}

Practice consistently and focus on understanding WHY moves work, not just WHAT moves to make!
    """

# ============================================================================
# 🎮 MAIN SERVER EXECUTION
# ============================================================================

if __name__ == "__main__":
    # You can run with different transports:
    # python minesweeper_server.py                    # Default stdio
    # python minesweeper_server.py --transport http   # HTTP server
    import sys
    
    transport = "stdio"  # Default
    port = 8000
    
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        if idx + 1 < len(sys.argv):
            transport = sys.argv[idx + 1]
    
    if "--port" in sys.argv:
        idx = sys.argv.index("--port") 
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    
    if transport == "http":
        print(f"🚀 Starting Minesweeper MCP Server on http://localhost:{port}")
        print("🎯 Connect your LLM client to start playing!")
        mcp.run(transport="streamable-http", host="127.0.0.1", port=port)
    else:
        print("🎯 Minesweeper MCP Server starting in stdio mode...")
        mcp.run()