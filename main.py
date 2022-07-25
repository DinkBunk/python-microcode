import gc
gc.collect()
import microdot
import request

app = microdot.Microdot()

htmldoc = '''<!DOCTYPE html>
<html>
    <head>
        <title>Microdot Example Page</title>
    </head>
    <body>
        <div>
            <h1>Microdot Example Page</h1>
            <p>Hello from Microdot!</p>
            <p><a href="/shutdown">Click to shutdown the server</a></p>
        </div>
    </body>
</html>
'''


@app.route('/')
def hello(request: request.Request):
    return htmldoc, 200, {'Content-Type': 'text/html'}


@app.route('/shutdown')
def shutdown(request: request.Request):
    request.app.shutdown()
    return 'The server is shutting down...'


app.run(debug=True)