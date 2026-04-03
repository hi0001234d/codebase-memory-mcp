#!/usr/bin/env python3
"""
Performance Benchmark Script for Codebase-Memory-MCP (Pagination feature)
--------------------------------------------------------------------------
This script generates an empirical benchmark comparing the LLM Token overhead 
of standard unbounded Graph Traversal vs the newly implemented Server-Side Pagination.
It provisions a massive mock codebase, runs the MCP plugin, measures serialized 
payload sizes, and outputs a mathematical reduction report.

Usage: 
    python3 generate_benchmark_report.py
"""

import subprocess
import json
import math
import shutil
import os
import sys

# Configurations
DUMMY_REPO_PATH = "/tmp/woo_benchmark_mcp"
MCP_BINARY = "./build/c/codebase-memory-mcp"
TOKENS_PER_BYTE_HEURISTIC = 4 # Standard LLM text approximation
COST_PER_1K_TOKENS = 0.003    # Standard Claude 3.5 Sonnet Input Cost

def setup():
    print("[1/3] Environment: Cleaning and Provisioning massive dummy repository...")
    if os.path.exists(DUMMY_REPO_PATH):
        shutil.rmtree(DUMMY_REPO_PATH)
    os.makedirs(DUMMY_REPO_PATH)

def generate_mock_architecture():
    print("[2/3] Provisioning AST: Injecting 150+ functions and monolithic dependencies...")
    code = ""
    # Generate 150 mock dependencies
    for i in range(1, 151):
        code += f"function dependencyWorker{i}() {{ /* complex logic */ }}\n"
        
    # Scenario 1
    code += "\nfunction ControllerShallow() {\n"
    for i in range(1, 6): code += f"  dependencyWorker{i}();\n"
    code += "}\n"

    # Scenario 2
    code += "\nfunction ControllerDeep() {\n"
    for i in range(1, 26): code += f"  dependencyWorker{i}();\n"
    code += "}\n"

    # Scenario 3
    code += "\nfunction MassiveClass() {\n"
    for i in range(1, 61): code += f"  dependencyWorker{i}();\n"
    code += "}\n"

    # Scenario 4
    code += "\nfunction InitializationHook() {\n"
    for i in range(1, 16): code += f"  dependencyWorker{i}();\n"
    code += "}\n"

    # Scenario 5
    code += "\nfunction DatabaseMigrations() {\n"
    for i in range(1, 121): code += f"  dependencyWorker{i}();\n"
    code += "}\n"

    # Scenario 6
    code += "\nfunction MiddlewareFilter() {\n"
    for i in range(1, 4): code += f"  dependencyWorker{i}();\n"
    code += "}\n"

    # Scenario 7
    code += "\nfunction EventDispatcher() {\n"
    for i in range(1, 46): code += f"  dependencyWorker{i}();\n"
    code += "}\n"

    with open(f"{DUMMY_REPO_PATH}/main.js", "w") as f:
        f.write(code)

    # Initialize Git (Required by CBM for indexing)
    subprocess.run(["git", "init"], cwd=DUMMY_REPO_PATH, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "add", "main.js"], cwd=DUMMY_REPO_PATH, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "benchmark@team.com"], cwd=DUMMY_REPO_PATH, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.name", "Benchmark Script"], cwd=DUMMY_REPO_PATH, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "commit", "-m", "init architecture"], cwd=DUMMY_REPO_PATH, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def index_repository():
    print("[3/3] Compiling Schema: Indexing via codebase-memory-mcp SQLite parser...\n")
    if not os.path.exists(MCP_BINARY):
        print(f"Error: {MCP_BINARY} not found. Please compile with 'make -f Makefile.cbm cbm'")
        sys.exit(1)
        
    cmd = [MCP_BINARY, "cli", "index_repository", f'{{"repo_path":"{DUMMY_REPO_PATH}"}}']
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def query_payload_size(func_name, paginated=False):
    q = {"project": "tmp-woo_benchmark_mcp", "function_name": func_name}
    if paginated:
        q["page"] = 1
        q["page_size"] = 5
        
    cmd = [MCP_BINARY, "cli", "trace_call_path", json.dumps(q)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stdout
    if 'content' in out:
        # Measure serialized payload chunk mapped correctly
        return len(out)
    return 0

def run_analytics():
    scenarios = [
        ("Trace Call Path: Controller (Shallow, 5 calls)", "ControllerShallow"),
        ("Trace Call Path: Admin Controller (Deep, 25 calls)", "ControllerDeep"),
        ("Trace Call Path: Controller (Massive, 60 calls)", "MassiveClass"),
        ("Trace Call Path: Initialization Hook (15 calls)", "InitializationHook"),
        ("Trace Call Path: Database Migrations (120 calls)", "DatabaseMigrations"),
        ("Trace Call Path: Middleware Filter (3 calls)", "MiddlewareFilter"),
        ("Trace Call Path: Event Dispatcher (45 calls)", "EventDispatcher"),
    ]

    results = []
    print("Executing Analytics Engine (Live Queries)....\n")
    print("-" * 115)
    print(f"| {'#':<2} | {'Scenario Analysis Title':<50} | {'Tokens A':<8} | {'Tokens B':<8} | {'Token Savings':<13} |")
    print("-" * 115)

    for idx, (name, func) in enumerate(scenarios):
        # Math & Heuristics logic
        len_a = query_payload_size(func, False)
        len_b = query_payload_size(func, True)
        
        tok_a = math.ceil(len_a / TOKENS_PER_BYTE_HEURISTIC)
        tok_b = math.ceil(len_b / TOKENS_PER_BYTE_HEURISTIC)
        
        save_pct = ((tok_a - tok_b) / tok_a * 100) if tok_a > 0 else 0
        
        results.append({
            "No": idx+1, "Scenario": name, "Tokens A": tok_a, 
            "Tokens B": tok_b, "Savings": save_pct
        })
        
        print(f"| {idx+1:<2} | {name:<50} | {tok_a:<8} | {tok_b:<8} | {save_pct:>12.2f}% |")

    print("-" * 115)
    
    tot_a = sum(r["Tokens A"] for r in results)
    tot_b = sum(r["Tokens B"] for r in results)
    tot_sav = ((tot_a - tot_b) / tot_a * 100) if tot_a > 0 else 0
    
    cost_a = (tot_a / 1000) * COST_PER_1K_TOKENS
    cost_b = (tot_b / 1000) * COST_PER_1K_TOKENS
    
    print("\n===============================")
    print("   OVERALL IMPACT SUMMARY      ")
    print("===============================")
    print(f"Total Standard Tokens : {tot_a:,}")
    print(f"Total Paginated Tokens: {tot_b:,}")
    print(f"API Cost (Standard)   : ${cost_a:.4f}")
    print(f"API Cost (Paginated)  : ${cost_b:.4f}")
    print(f"OVERALL EFFICIENCY    : {tot_sav:.2f}% COST SAVINGS")
    print("===============================\n")

if __name__ == "__main__":
    setup()
    generate_mock_architecture()
    index_repository()
    run_analytics()
