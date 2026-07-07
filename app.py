from flask import Flask
import logging

from iam.application.services import AuthApplicationService
from iam.interfaces.services import iam_api
from shared.infrastructure.database import init_db
from wellness.interfaces.services import wellness_api

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.register_blueprint(iam_api)
app.register_blueprint(wellness_api)

first_request = True

@app.before_request
def setup():
    """
    Initialize the database and create a test device on the first request.
    :return: None
    """
    global first_request
    if first_request:
        first_request = False
        init_db()
        auth_application_service = AuthApplicationService()
        auth_application_service.get_or_create_test_device()

@app.route('/')
def about_edge_service():
    """
        Show information about the edge service.
        :return: A string containing information about the edge service.
        """
    return "Octane IoT Edge Service - Octane Application"

if __name__ == '__main__':
    app.run(host='0.0.0.0' ,debug=True)