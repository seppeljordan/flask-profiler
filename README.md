# Flask-profiler

Flask-profiler measures endpoints defined in your flask application;
and provides you fine-grained report through a web interface.

It gives answers to these questions:
* Where are the bottlenecks in my application?
* Which endpoints are the slowest in my application?
* Which are the most frequently called endpoints?
* What causes my slow endpoints? In which context, with what args and
  kwargs are they slow?
* How much time did a specific request take?

In short, if you are curious about what your endpoints are doing and
what requests they are receiving, give a try to flask-profiler.

With flask-profiler's web interface, you can monitor all your
endpoints' performance and investigate endpoints and received requests
by drilling down through filters.

## Quick Start
It is easier to understand flask-profiler going through an
example. Let's dive in.

Install flask-profiler by pip.
```sh
pip install flask_profiler
```


Edit your code where you are creating Flask app.
```python
# your app.py
from flask import Flask
import flask_profiler

app = Flask(__name__)
app.config["DEBUG"] = True

# You need to declare necessary configuration to initialize
# flask-profiler as follows:
app.config["flask_profiler"] = {
    "enabled": app.config["DEBUG"],
    "basicAuth":{
        "enabled": True,
        "username": "admin",
        "password": "admin"
    },
    "ignore": [
        "^/static/.*"
    ]
}


@app.route('/product/<id>', methods=['GET'])
def getProduct(id):
    return "product id is " + str(id)


@app.route('/product/<id>', methods=['PUT'])
def updateProduct(id):
    return "product {} is being updated".format(id)


@app.route('/products', methods=['GET'])
def listProducts():
    return "suppose I send you product list..."

@app.route('/static/something/', methods=['GET'])
def staticSomething():
    return "this should not be tracked..."

# In order to activate flask-profiler, you have to pass flask
# app as an argument to init_app.
# All the endpoints declared so far will be tracked by flask-profiler.
flask_profiler.init_app(app)


# endpoint declarations after flask_profiler.init_app() will be
# hidden to flask_profiler.
@app.route('/doSomething', methods=['GET'])
def doSomething():
    return "flask-profiler will not measure this."


# But in case you want an endpoint to be measured by flask-profiler,
# you can specify this explicitly by using profile() decorator
@app.route('/doSomethingImportant', methods=['GET'])
@flask_profiler.profile()
def doSomethingImportant():
    return "flask-profiler will measure this request."

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)


```

Now run your `app.py`
```
python app.py
```

And make some requests like:
```sh
curl http://127.0.0.1:5000/products
curl http://127.0.0.1:5000/product/123
curl -X PUT -d arg1=val1 http://127.0.0.1:5000/product/123
```

If everything is okay, Flask-profiler will measure these requests. You
can see the result heading to http://127.0.0.1:5000/flask-profiler/ or
get results as JSON
http://127.0.0.1:5000/flask-profiler/api/measurements?sort=elapsed,desc

## SQLite
```json
app.config["flask_profiler"] = {
    "storage": {
        "FILE": "flask_profiler.sql",
    }
}
```

Below the other options are listed.

| Filter key   |      Description      |  Default |
|----------|-------------|------|
| storage.FILE | SQLite database file name | flask_profiler.sql|

### Sampling

Control the number of samples taken by flask-profiler

You would want control over how many times should the flask profiler
take samples while running in production mode.  You can supply a
function and control the sampling according to your business logic.

Example 1: Sample 1 in 100 times with random numbers
```python
app.config["flask_profiler"] = {
    "sampling_function": lambda: True if random.sample(list(range(1, 101)), 1) == [42] else False
}
```

Example 2: Sample for specific users
```python
app.config["flask_profiler"] = {
    "sampling_function": lambda: True if user is 'divyendu' else False
}
```

If sampling function is not present, all requests will be sampled.

### Changing flask-profiler endpoint root

By default, we can access flask-profiler at <your-app>/flask-profiler

```python
app.config["flask_profiler"] = {
        "endpointRoot": "secret-flask-profiler"
}
```

### Ignored endpoints

Flask-profiler will try to track every endpoint defined so far when
`flask_profiler.init_app()` is invoked. If you want to exclude some of
the endpoints, you can define matching regex for them as follows:

```python
app.config["flask_profiler"] = {
        "ignore": [
            "^/static/.*",
            "/api/users/\w+/password"
        ]
}
```


## Authors
* [Musafa Atik](https://www.linkedin.com/in/muatik)
* Fatih Sucu
* [Safa Yasin Yildirim](https://www.linkedin.com/in/safayasinyildirim)

## License
MIT
