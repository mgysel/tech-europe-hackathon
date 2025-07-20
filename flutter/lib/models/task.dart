import 'package:cloud_firestore/cloud_firestore.dart';

class Task {
  final String id;
  final String instruction;
  final DateTime createdAt;

  Task({required this.id, required this.instruction, required this.createdAt});

  factory Task.fromDoc(DocumentSnapshot<Map<String, dynamic>> doc) {
    final data = doc.data() ?? {};
    final ts = data['createdAt'] as Timestamp?;
    return Task(
      id: doc.id,
      instruction: data['instruction'] as String? ?? '',
      createdAt: ts?.toDate() ?? DateTime.now(),
    );
  }
}
