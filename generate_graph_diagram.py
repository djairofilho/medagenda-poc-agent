"""
Generate LangGraph diagram and PNG image.

Uses:
1. LangGraph native Mermaid export
2. Mermaid.ink API to generate PNG
"""

import requests
import base64
import json
from pathlib import Path
from app.agent.graph import build_graph

def generate_mermaid_diagram():
    """Generate Mermaid diagram from LangGraph."""
    
    # Build the graph
    print("🔨 Building LangGraph workflow...")
    graph = build_graph()
    
    # Get Mermaid representation
    print("📊 Generating Mermaid diagram...")
    mermaid_code = graph.get_graph().draw_mermaid()
    
    # Save to file in root directory
    output_file = Path("langgraph_diagram.mmd")
    output_file.write_text(mermaid_code, encoding="utf-8")
    
    print(f"✅ Mermaid diagram saved to: {output_file}")
    
    return mermaid_code

def generate_png_from_mermaid(mermaid_code):
    """Generate PNG image from Mermaid code using mermaid.ink API."""
    
    print("\n🖼️  Generating PNG image...")
    
    try:
        # Encode mermaid code to base64
        encoded = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
        
        # Use mermaid.ink API
        url = f"https://mermaid.ink/img/{encoded}"
        
        print(f"📡 Fetching image from mermaid.ink...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # Save PNG in root directory
            output_png = Path("langgraph_diagram.png")
            output_png.write_bytes(response.content)
            print(f"✅ PNG image saved to: {output_png}")
            return True
        else:
            print(f"❌ Failed to generate image: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating PNG: {e}")
        return False

def main():
    """Main function."""
    print("="*60)
    print("LANGGRAPH DIAGRAM GENERATOR")
    print("="*60)
    
    # Generate Mermaid code
    mermaid_code = generate_mermaid_diagram()
    
    # Print the code
    print("\n" + "="*60)
    print("MERMAID CODE:")
    print("="*60)
    print(mermaid_code)
    print("="*60)
    
    # Generate PNG
    success = generate_png_from_mermaid(mermaid_code)
    
    # Final instructions
    print("\n" + "="*60)
    print("📚 NEXT STEPS:")
    print("="*60)
    
    if success:
        print("✅ Diagram generated successfully!")
        print("\n📁 Files created:")
        print("   - langgraph_diagram.mmd (Mermaid code)")
        print("   - langgraph_diagram.png (PNG image)")
    else:
        print("⚠️  PNG generation failed. Alternative options:")
        print("\n1. Use Mermaid Live Editor:")
        print("   https://mermaid.live/")
        print("   (Copy and paste the code above)")
        
        print("\n2. Install mermaid-cli locally:")
        print("   npm install -g @mermaid-js/mermaid-cli")
        print("   mmdc -i langgraph_diagram.mmd -o langgraph_diagram.png")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
