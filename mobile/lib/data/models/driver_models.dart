/// Maps the backend `app/api/v1/endpoints/driver.py` request bodies.
class DriverLocationRequest {
  final double latitude;
  final double longitude;

  const DriverLocationRequest({required this.latitude, required this.longitude});

  Map<String, dynamic> toJson() => {
        'latitude': latitude,
        'longitude': longitude,
      };
}

class DriverStatusUpdateRequest {
  final String status;

  const DriverStatusUpdateRequest({required this.status});

  Map<String, dynamic> toJson() => {'status': status};
}
