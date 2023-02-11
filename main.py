import argparse

from imuEhall import ImuEhall

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', type=str, default=None)
    parser.add_argument('--password', type=str, default=None)
    parser.add_argument('--sendurl', type=str, default="")

    args=parser.parse_args()
    app = ImuEhall(args.username,args.password,args.sendurl)
    if app.login():
        app.sign()
    app.send_to_server()
