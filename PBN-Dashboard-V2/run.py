import sys
import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    print(f"Starting PBN Management Dashboard V2 on http://{HOST}:{PORT}")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False, workers=1)
