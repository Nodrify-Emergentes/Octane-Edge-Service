from flask import Blueprint, request, jsonify
import requests
from iam.interfaces.services import authenticate_request
from wellness.application.services import VehicleMetricRecordApplicationService

wellness_api = Blueprint('wellness', __name__, url_prefix='/api/v1')

vehicle_metric_service = VehicleMetricRecordApplicationService()

@wellness_api.route('/metrics', methods=["POST"])
def create_vehicle_metric_record():
    """
    Endpoint to create a new vehicle metric record and forward to external API.
    Expects a JSON payload with device_id, vehicle_id, latitude, longitude,
    CO2Ppm, NH3Ppm, BenzenePpm, temperatureCelsius, humidityPercentage,
    pressureHpa, impactDetected.
    Requires an Authorization header with Bearer token.

    :return: A JSON response with the created vehicle metric record.
    201 if successful, 400 for invalid request, 401 for authentication failure.
    """
    try:
        # Validate Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token no proporcionado'}), 401

        api_key = auth_header.split(' ')[1]
        data = request.json

        device_id = data["deviceId"]

        # Authenticate device using AuthApplicationService
        from iam.application.services import AuthApplicationService
        auth_service = AuthApplicationService()

        if not auth_service.authenticate_device(device_id, api_key):
            return jsonify({'error': 'Autenticación fallida'}), 401

        # Extract data from request
        vehicle_id = data["vehicleId"]
        latitude = data["latitude"]
        longitude = data["longitude"]
        CO2Ppm = data["CO2Ppm"]
        NH3Ppm = data["NH3Ppm"]
        BenzenePpm = data["BenzenePpm"]
        temperatureCelsius = data["temperatureCelsius"]
        pressureHpa = data["pressureHpa"]
        impactDetected = data["impactDetected"]

        # Create local vehicle metric record
        record = vehicle_metric_service.create_vehicle_metric_record(
            device_id, vehicle_id, latitude, longitude, CO2Ppm, NH3Ppm,
            BenzenePpm, temperatureCelsius, pressureHpa,
            impactDetected
        )

        # Assemble payload for external API
        import requests

        api_url = "https://strong-surprise-production-ef50.up.railway.app/api/v1/metrics"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "vehicleId": vehicle_id,
            "latitude": latitude,
            "longitude": longitude,
            "CO2Ppm": CO2Ppm,
            "NH3Ppm": NH3Ppm,
            "BenzenePpm": BenzenePpm,
            "temperatureCelsius": temperatureCelsius,
            "pressureHpa": pressureHpa,
            "impactDetected": impactDetected
        }

        # Send data to external API
        external_response = requests.post(api_url, json=payload, headers=headers, timeout=10)

        # Return response including external API status
        return jsonify({
            "id": record.id,
            "deviceId": record.device_id,
            "vehicleId": record.vehicle_id,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "CO2Ppm": record.CO2Ppm,
            "NH3Ppm": record.NH3Ppm,
            "BenzenePpm": record.BenzenePpm,
            "temperatureCelsius": record.temperatureCelsius,
            "pressureHpa": record.pressureHpa,
            "impactDetected": record.impactDetected,
            "external_api_status": external_response.status_code
        }), 201

    except KeyError as e:
        return jsonify({"error": f"Campo faltante: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.Timeout:
        return jsonify({"error": "Timeout al conectar con API externa"}), 504
    except requests.RequestException as e:
        return jsonify({"error": f"Error al conectar con API externa: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# def create_vehicle_metric_record():
#     """
#     Endpoint to create a new vehicle metric record.
#     Expects a JSON payload with device_id, vehicle_id, latitude, longitude,
#     CO2Ppm, NH3Ppm, BenzenePpm, temperatureCelsius, humidityPercentage,
#     pressureHpa, impactDetected.
#     Requires an X-API-Key header with the API key.
#
#     :return: A JSON response with the created vehicle metric record with its ID.
#     201 if the record is created successfully, else 400 if the request is invalid or authentication fails.
#     """
#
#     auth_result = authenticate_request()
#     if auth_result:
#         return auth_result
#     data = request.json
#     try:
#         device_id = data["device_id"]
#         vehicle_id = data["vehicle_id"]
#         latitude = data["latitude"]
#         longitude = data["longitude"]
#         CO2Ppm = data["CO2Ppm"]
#         NH3Ppm = data["NH3Ppm"]
#         BenzenePpm = data["BenzenePpm"]
#         temperatureCelsius = data["temperatureCelsius"]
#         humidityPercentage = data["humidityPercentage"]
#         pressureHpa = data["pressureHpa"]
#         impactDetected = data["impactDetected"]
#
#         record = vehicle_metric_service.create_vehicle_metric_record(
#             device_id, vehicle_id, latitude, longitude, CO2Ppm, NH3Ppm,
#             BenzenePpm, temperatureCelsius, humidityPercentage, pressureHpa,
#             impactDetected, request.headers.get("X-API-Key")
#         )
#
#         return jsonify({
#             "id": record.id,
#             "device_id": record.device_id,
#             "vehicle_id": record.vehicle_id,
#             "latitude": record.latitude,
#             "longitude": record.longitude,
#             "CO2Ppm": record.CO2Ppm,
#             "NH3Ppm": record.NH3Ppm,
#             "BenzenePpm": record.BenzenePpm,
#             "temperatureCelsius": record.temperatureCelsius,
#             "humidityPercentage": record.humidityPercentage,
#             "pressureHpa": record.pressureHpa,
#             "impactDetected": record.impactDetected
#         }), 201
#     except KeyError as e:
#         return jsonify({"error": f"Missing field: {str(e)}"}), 400
#     except ValueError as e:
#         return jsonify({"error": str(e)}), 400