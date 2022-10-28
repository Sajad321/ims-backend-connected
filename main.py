import uvicorn

from config import create_app

app = create_app()

if __name__ == '__main__':
    if(not os.path.exists(os.path.join(os.getenv('LOCALAPPDATA'), 'ims'))):
        os.mkdir(os.path.join(os.getenv('LOCALAPPDATA'),
                              'ims'))
    if(not os.path.exists(os.path.join(os.getenv('LOCALAPPDATA'), 'ims', "images"))):
        os.mkdir(os.path.join(os.getenv('LOCALAPPDATA'),
                              'ims', "images"))
    if(not os.path.exists(os.path.join(os.getenv('LOCALAPPDATA'), 'ims', "qr"))):
        os.mkdir(os.path.join(os.getenv('LOCALAPPDATA'),
                              'ims', "qr"))
    uvicorn.run(app)
