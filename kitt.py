#!/usr/bin/env python3
"""KITT — Kauz Intelligent Task Tracker"""
import sys
from agent import main, signal_loop

if __name__ == "__main__":
    if "--signal" in sys.argv:
        signal_loop()
    else:
        main()
