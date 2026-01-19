from main import app
import json

try:
    schema = app.openapi()
    print("OpenAPI schema generated successfully!")
    print(f"Number of paths: {len(schema.get('paths', {}))}")
    print(f"Number of components: {len(schema.get('components', {}).get('schemas', {}))}")
except Exception as e:
    print(f"Error generating OpenAPI schema: {e}")
    import traceback
    traceback.print_exc()

