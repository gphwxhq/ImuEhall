from imuEhall import ImuEhall

if __name__ == '__main__':
    app=ImuEhall()
    if app.login():
        app.sign()
    app.send_to_server()
