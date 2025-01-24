from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Optional, Any
import threading
import os
import time
from pynput.keyboard import Key, Controller, KeyCode

from main import PreciseActionRecorder

app = FastAPI()
recorder = PreciseActionRecorder()
keyboard = Controller()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/start-recording")
async def start_recording():
    try:
        # Start recording in a separate thread
        recording_thread = threading.Thread(target=recorder.start_recording)
        recording_thread.start()
        return {"status": "success", "message": "Recording started. Press 'Esc' to stop."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pause-recording")
async def pause_recording():
    try:
        # Only press the P key
        keyboard.press('p')
        time.sleep(0.1)  # Small delay to ensure key press is registered
        keyboard.release('p')  # Release after press
        return {"status": "success", "message": "Recording paused"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/unpause-recording")
async def unpause_recording():
    try:
        # Press and release P key again
        keyboard.press('p')
        time.sleep(0.1)  # Small delay to ensure key press is registered
        keyboard.release('p')
        return {"status": "success", "message": "Recording resumed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-recording")
async def stop_recording():
    try:
        # Press the Esc key
        keyboard.press(Key.esc)
        print("Esc key pressed")
        time.sleep(1)  # Hold the key for 1 second
        
        # Release the Esc key
        keyboard.release(Key.esc)
        print("Esc key released")
        
        recorder.recording = False
        return {"status": "success", "message": "Recording stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-recordings")
async def list_recordings():
    try:
        recordings = recorder.list_recordings()
        recordings_with_paths = [
            {
                "name": rec,
                "path": os.path.join(recorder.log_dir, rec)
            }
            for rec in recordings
        ]
        return {"recordings": recordings_with_paths}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/replay-recording")
async def replay_recording(data: Dict[str, str]):
    try:
        recording_path = data.get("path")
        if not recording_path or not os.path.exists(recording_path):
            raise HTTPException(status_code=404, detail="Recording not found")
        
        # Reset stop flag before starting new replay
        recorder.stop_replay = False
        
        def start_replay():
            try:
                recorder.replay_events(
                    log_file=recording_path,
                    precision_mode=True,
                    filter_events=None,
                    loop_count=1
                )
            except Exception as e:
                print(f"Replay error: {e}")

        # Start replay in a separate thread
        replay_thread = threading.Thread(target=start_replay)
        replay_thread.start()
        
        return {"status": "success", "message": "Replay started. Press 'Ctrl+S' to stop."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/replay-recording-with-options")
async def replay_recording_with_options(data: Dict[str, Any]):
    try:
        recording_path = data.get("path")
        precision_mode = data.get("precision", True)
        loop_enabled = data.get("loop_enabled", False)
        loop_count = data.get("loop_count", 1)

        if not recording_path or not os.path.exists(recording_path):
            raise HTTPException(status_code=404, detail="Recording not found")
        
        if loop_enabled and (loop_count < 2 or loop_count > 10):
            raise HTTPException(status_code=400, detail="Loop count must be between 2 and 10")

        # Reset stop flag before starting new replay
        recorder.stop_replay = False
        
        def start_replay():
            try:
                recorder.replay_events(
                    log_file=recording_path,
                    precision_mode=precision_mode,
                    filter_events=None,
                    loop_count=loop_count
                )
            except Exception as e:
                print(f"Replay error: {e}")

        # Start replay in a separate thread
        replay_thread = threading.Thread(target=start_replay)
        replay_thread.start()
        
        return {
            "status": "success", 
            "message": f"Replay started with {'precise timing' if precision_mode else 'normal timing'}" +
                      f"{f' and {loop_count} loops' if loop_enabled else ''}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-replay")
async def stop_replay():
    try:
        recorder.stop_replay = True
        return {"status": "success", "message": "Replay stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
