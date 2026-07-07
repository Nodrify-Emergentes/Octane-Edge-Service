import requests
from flask import Blueprint, request, jsonify

from iam.application.services import AuthApplicationService

iam_api = Blueprint('iam_api', __name__, url_prefix='/api/v1')

# Initialize the AuthApplicationService
auth_service = AuthApplicationService()

def authenticate_request():
    """
    Authenticate a request using the device_id and API key.

    Checks for the presence of the device_id in the body, and API key in the request headers.
    :return: None if authentication is successful, else a JSON response with an error message.
    """
    device_id = request.json.get('deviceId') if request.json else None
    api_key = request.headers.get('X-API-Key')
    if not device_id or not api_key:
        return jsonify({'error': 'Missing device_id or API key'}), 401
    if not auth_service.authenticate(device_id, api_key):
        return jsonify({'error': 'Invalid device_id or API key'}), 401
    return None


@iam_api.route('/devices/authentication/register', methods=['POST'])
def register_device():
    """
    Register a new device with the backend and store locally.

    Expected JSON body:
    {
      "deviceId": "string",
      "vehicleId": 0
    }

    Backend returns:
    {
      "id": 0,
      "deviceId": "string",
      "vehicleId": 0,
      "token": "string"
    }

    Returns:
    - 201: Device registered successfully with token
    - 400: Missing required fields
    - 503: Backend connection error
    """
    try:
        data = request.json
        device_id = data["deviceId"]
        vehicle_id = data["vehicleId"]

        # Forward registration to Bykerz backend
        backend_url = "https://strong-surprise-production-ef50.up.railway.app/api/v1/devices/authentication/register"
        #backend_url = "http://localhost:8080/api/v1/devices/authentication/register"
        response = requests.post(
            backend_url,
            json={"deviceId": device_id, "vehicleId": vehicle_id},
            timeout=10
        )

        if response.status_code in (200,201):
            # Backend returns { "id": 0, "deviceId": "...", "vehicleId": 0, "token": "..." }
            backend_data = response.json()
            api_key = backend_data["token"]  # Extract token from response

            # Store device locally in edge database
            from iam.infrastructure.models import Device as DeviceModel
            from datetime import datetime

            device, created = DeviceModel.get_or_create(
                device_id=device_id,
                defaults={
                    'api_key': api_key,
                    'created_at': datetime.now()
                }
            )

            # Always update the api_key to the one from the backend
            if not created:
                device.api_key = api_key
                device.save()



            return jsonify(backend_data), response.status_code
        else:
            return jsonify({"error": "Backend registration failed", "details": response.text}), response.status_code

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400
    except requests.Timeout:
        return jsonify({"error": "Backend connection timeout"}), 504
    except requests.RequestException as e:
        return jsonify({"error": f"Backend connection error: {str(e)}"}), 503


@iam_api.route('/devices/authentication/validate', methods=['POST'])
def validate_device():
    """
    Validate an existing device with the backend and store/update locally.

    Expected JSON body:
    {
      "deviceId": "string"
    }

    Backend returns (on success):
    {
      "id": 0,
      "deviceId": "string",
      "vehicleId": 0,
      "token": "string"
    }

    Returns:
    - 200: Device validated successfully with token
    - 404: Device not found in backend
    - 400: Missing required fields
    - 503: Backend connection error
    """
    try:
        data = request.json
        device_id = data["deviceId"]

        # Call backend validation endpoint
        #backend_url = "http://localhost:8080/api/v1/devices/authentication/validate"
        backend_url = "https://strong-surprise-production-ef50.up.railway.app/api/v1/devices/authentication/validate"
        response = requests.post(
            backend_url,
            json={"deviceId": device_id},
            timeout=10
        )

        if response.status_code == 200:
            # Backend returns { "id": 0, "deviceId": "...", "vehicleId": 0, "token": "..." }
            backend_data = response.json()
            api_key = backend_data["token"]

            # Store or update device locally in edge database
            from iam.infrastructure.models import Device as DeviceModel
            from datetime import datetime

            device, created = DeviceModel.get_or_create(
                device_id=device_id,
                defaults={
                    'api_key': api_key,
                    'created_at': datetime.now()
                }
            )

            # Update api_key if device already exists
            if not created:
                device.api_key = api_key
                device.save()

            return jsonify(backend_data), 200

        elif response.status_code == 404:
            return jsonify({"error": "Device not found in backend"}), 404
        else:
            return jsonify({"error": "Backend validation failed", "details": response.text}), response.status_code

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400
    except requests.Timeout:
        return jsonify({"error": "Backend connection timeout"}), 504
    except requests.RequestException as e:
        return jsonify({"error": f"Backend connection error: {str(e)}"}), 503
