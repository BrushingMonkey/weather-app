from flask import Flask, jsonify, request, redirect, render_template, url_for
from prometheus_client import make_wsgi_app, Counter, Histogram
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import time
from datetime import datetime
from deep_translator import GoogleTranslator
from modules import backend

app = Flask(__name__)

# Set up metrics collection
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

REQUEST_COUNT = Counter(
    'app_request_count',
    'Application Request Count',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Application Request Latency',
    ['method', 'endpoint']
)

REQUEST_LOCATION_COUNT = Counter(
    'location_request_count',
    'Application Request Count',
    ['method', 'endpoint', 'location']
)

HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint']
)

@app.route("/", methods=["POST", "GET"])
def user_input():
    start_time = time.time()

    if request.method == "POST":
        location = request.form.get("location").lower()
        time_now = datetime.today()
        REQUEST_LOCATION_COUNT.labels('GET', '/', location).inc()

        weather_data = backend.get_api(location)

        if weather_data == "error":
            return render_template("home.html", error=True)

        filtered_json = backend.filter_api(weather_data)

        translated_location = GoogleTranslator(source='auto', target='en').translate(weather_data['resolvedAddress'])

        backend.create_json_file(filtered_json)

        return redirect(url_for(".display", location=translated_location))

    # Record GET request
    # REQUEST_COUNT.labels('GET', '/', 200).inc()
    return render_template("home.html")

@app.route("/display")
def display():
    start_time = time.time()

    location = request.args.get('location')
    json_file = backend.read_json_file()

    # Record successful response
    HTTP_REQUESTS_TOTAL.labels(request.method, '/display').inc()
    REQUEST_LOCATION_COUNT.labels('GET', '/display', location).inc()
    REQUEST_LATENCY.labels('GET', '/display').observe(time.time() - start_time)

    return render_template("display.html", json_file=json_file, location=location)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
