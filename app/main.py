from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/some-endpoint")
async def some_endpoint(param: str):
    try:
        # Your logic here
        pass
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid value provided.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/another-endpoint")
async def another_endpoint(data: dict):
    try:
        # Your logic here
        pass
    except KeyError:
        raise HTTPException(status_code=400, detail="Missing key in input data.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add similar error handling for all other endpoints in the application