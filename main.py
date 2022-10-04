from website import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app,debug=True) #Change to app.run(debug=True) to run on Heroku.
