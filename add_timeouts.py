#!/usr/bin/env python3
"""
Script to add timeout protection to Ollama calls in the notebook.
"""

import json
import sys

def add_timeouts_to_notebook(notebook_path):
    """Add timeout protection to get_ollama_response and related functions."""
    
    # Read notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    # Find the cell with get_ollama_response
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Check if this is the Ollama integration cell
            if 'def get_ollama_response' in source and 'timeout' not in source:
                print("Found get_ollama_response - adding timeout...")
                
                # Replace the function
                old_func = '''def get_ollama_response(prompt: str, model: str = OLLAMA_MODEL, system_prompt: str = None) -> str:
    """Get a response from Ollama."""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = ollama.chat(model=model, messages=messages)
        return response['message']['content']
    except Exception:
        return None'''
                
                new_func = '''def get_ollama_response(prompt: str, model: str = OLLAMA_MODEL, system_prompt: str = None, timeout: int = 30) -> str:
    """Get a response from Ollama with timeout protection."""
    try:
        from threading import Thread
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Store result in list (mutable)
        result = [None]
        error = [None]
        
        def make_request():
            try:
                response = ollama.chat(model=model, messages=messages)
                result[0] = response['message']['content']
            except Exception as e:
                error[0] = e
        
        # Start request in thread with timeout
        thread = Thread(target=make_request)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            print(f"\\n⏱️  Ollama timed out after {timeout}s")
            return None
        
        if error[0]:
            print(f"\\n❌ Ollama error: {error[0]}")
            return None
            
        return result[0]
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        return None'''
                
                # Replace in source
                new_source = source.replace(old_func, new_func)
                
                # Update parse_question_with_ollama to add verbose and progress
                if 'def parse_question_with_ollama' in new_source:
                    print("Updating parse_question_with_ollama...")
                    new_source = new_source.replace(
                        'def parse_question_with_ollama(question: str) -> Dict:',
                        'def parse_question_with_ollama(question: str, verbose: bool = True) -> Dict:'
                    )
                    new_source = new_source.replace(
                        '    """Use Ollama to parse a weather question."""\n    try:',
                        '    """Use Ollama to parse a weather question."""\n    try:\n        if verbose:\n            print("🤖 Analyzing your question with AI...")'
                    )
                    new_source = new_source.replace(
                        '        response = get_ollama_response(user_prompt, system_prompt=system_prompt)',
                        '        response = get_ollama_response(user_prompt, system_prompt=system_prompt, timeout=20)\n        \n        if verbose:\n            print("✅ Question analyzed!")'
                    )
                
                # Update generate_response_with_ollama
                if 'def generate_response_with_ollama' in new_source:
                    print("Updating generate_response_with_ollama...")
                    new_source = new_source.replace(
                        'def generate_response_with_ollama(parsed_question: Dict, weather_data: Dict) -> str:',
                        'def generate_response_with_ollama(parsed_question: Dict, weather_data: Dict, verbose: bool = True) -> str:'
                    )
                    new_source = new_source.replace(
                        '    """Use Ollama to generate a natural language response."""\n    try:',
                        '    """Use Ollama to generate a natural language response."""\n    try:\n        if verbose:\n            print("🤖 Generating AI response...")'
                    )
                    
                # Convert back to list of lines
                cell['source'] = [line + '\n' for line in new_source.split('\n')]
                if cell['source'][-1] == '\n':
                    cell['source'][-1] = cell['source'][-1].rstrip('\n')
                
                print("✅ Updated Ollama functions with timeouts!")
                break
    
    # Write back
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    
    print(f"\n✅ Notebook updated: {notebook_path}")

if __name__ == '__main__':
    notebook_path = 'weather_advisor_app.ipynb'
    add_timeouts_to_notebook(notebook_path)
    print("\n🎉 Timeouts added successfully!")

