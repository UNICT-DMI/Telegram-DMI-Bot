from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydrive2.files import MediaIoReadable
from starlette.responses import ContentStream
from module.utils.drive_utils import drive_utils


app = FastAPI()

@app.get('/favicon.ico')
def favicon():
    'Serve the website favicon'
    return FileResponse('webapp/static/assets/logo.ico')

@app.get('/drive/folder')
def _(folder_id: str):
    'Returns content of a folder in the DMI Drive.'
    files = drive_utils.list_files(folder_id) or []
    keys = 'id', 'title', 'mimeType'
    response = JSONResponse([{key: file[key] for key in keys} for file in files])
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.get('/drive/file')
def _(file_id: str):
    'Returns content of a file in the DMI Drive.'
    file = drive_utils.get_file(file_id)
    if not file:
        return JSONResponse({'error': 'File not found.'}, status_code = 204)
    content = file.GetContentIOBuffer()
    return StreamingResponse(
        stream(content),
        media_type = file['mimeType'],
        headers = {
            # delivering it as a download
            'Content-Disposition': f"attachment; filename=\"{file['title']}\"",
            # making it accessible from web browsers
            'Access-Control-Allow-Origin': '*'
        }
    )

def stream(content: MediaIoReadable) -> ContentStream:
    chunk = True
    while chunk:
        chunk = content.read()
        if chunk:
            yield chunk

app.mount('/', StaticFiles(directory = 'webapp/dist/', html = True), name = 'dist')
