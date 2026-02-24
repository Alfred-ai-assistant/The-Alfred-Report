#!/usr/bin/env python3
"""
Cost Tracker for The Alfred Report

Tracks token usage per LLM call and estimates daily costs.
Sends Telegram summary after each report run.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

COST_LOG_DIR = Path("/home/alfred/repos/The-Alfred-Report/public/alfred-report/cost-logs")

# Anthropic Haiku 4.5 pricing (as of 2026-02)
HAIKU_INPUT_COST = 0.80 / 1_000_000    # $0.80 per million input tokens
HAIKU_OUTPUT_COST = 4.00 / 1_000_000   # $4.00 per million output tokens

class CostTracker:
    """Track token usage and estimate costs."""
    
    def __init__(self, report_date: str):
        self.report_date = report_date
        self.calls = []
        self.log_file = COST_LOG_DIR / f"{report_date}_costs.json"
        COST_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    def record_call(
        self, 
        section: str, 
        input_tokens: int, 
        output_tokens: int,
        cache_hit: bool = False,
        model: str = "claude-haiku-4-5"
    ):
        """Record an LLM call."""
        call = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "section": section,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_hit": cache_hit,
            "input_cost": input_tokens * HAIKU_INPUT_COST,
            "output_cost": output_tokens * HAIKU_OUTPUT_COST,
        }
        call["total_cost"] = call["input_cost"] + call["output_cost"]
        self.calls.append(call)
    
    def get_summary(self) -> dict:
        """Generate summary of all calls."""
        total_input = sum(c["input_tokens"] for c in self.calls)
        total_output = sum(c["output_tokens"] for c in self.calls)
        total_cost = sum(c["total_cost"] for c in self.calls)
        cache_hits = sum(1 for c in self.calls if c["cache_hit"])
        
        return {
            "date": self.report_date,
            "total_calls": len(self.calls),
            "cache_hits": cache_hits,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "estimated_cost_usd": round(total_cost, 4),
            "calls": self.calls
        }
    
    def save(self):
        """Save log to file."""
        summary = self.get_summary()
        with open(self.log_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def telegram_message(self) -> str:
        """Format a Telegram message with the summary."""
        summary = self.get_summary()
        
        msg = f"""🧮 *Alfred Report Daily Cost Summary*

📅 Report Date: {summary['date']}

*Token Usage:*
• Input: {summary['total_input_tokens']:,}
• Output: {summary['total_output_tokens']:,}
• Total: {summary['total_input_tokens'] + summary['total_output_tokens']:,}

*API Calls:*
• Total calls: {summary['total_calls']}
• Cache hits: {summary['cache_hits']}

💰 *Estimated Cost:* ${summary['estimated_cost_usd']:.4f}

*Per-Call Breakdown:*
"""
        for call in summary['calls']:
            status = "✅ CACHED" if call['cache_hit'] else "🌐 LIVE"
            msg += f"\n• {call['section']}: {call['input_tokens']:,}→{call['output_tokens']:,} {status} (${call['total_cost']:.4f})"
        
        return msg

# Global instance
_tracker: Optional[CostTracker] = None

def init_tracker(report_date: str):
    """Initialize global tracker."""
    global _tracker
    _tracker = CostTracker(report_date)

def record(section: str, input_tokens: int, output_tokens: int, cache_hit: bool = False):
    """Record an LLM call."""
    if _tracker:
        _tracker.record_call(section, input_tokens, output_tokens, cache_hit)

def get_telegram_message() -> str:
    """Get formatted Telegram message."""
    if not _tracker:
        return "No cost tracking data available"
    return _tracker.telegram_message()

def save_log():
    """Save the cost log."""
    if _tracker:
        _tracker.save()

if __name__ == "__main__":
    # Test
    tracker = CostTracker("2026-02-24")
    tracker.record_call("ai_news", 175000, 232, cache_hit=False)
    tracker.record_call("reddit", 100000, 149, cache_hit=False)
    print(tracker.telegram_message())
    tracker.save()
