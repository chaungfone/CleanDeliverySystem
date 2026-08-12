/// Maps the backend `app/models/user.py::UserResponse`.
///
/// `role` is one of: CUSTOMER | DRIVER | ADMIN | BRANCH_MANAGER.
class User {
  final String id;
  final String phoneNumber;
  final String fullName;
  final String role;
  final String createdAt;

  const User({
    required this.id,
    required this.phoneNumber,
    required this.fullName,
    required this.role,
    required this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id'] as String? ?? '',
        phoneNumber: json['phone_number'] as String? ?? '',
        fullName: json['full_name'] as String? ?? '',
        role: json['role'] as String? ?? 'CUSTOMER',
        createdAt: json['created_at'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'phone_number': phoneNumber,
        'full_name': fullName,
        'role': role,
        'created_at': createdAt,
      };

  bool get isDriver => role.toUpperCase() == 'DRIVER';
  bool get isAdmin => role.toUpperCase() == 'ADMIN';
  bool get isBranchManager => role.toUpperCase() == 'BRANCH_MANAGER';
}
