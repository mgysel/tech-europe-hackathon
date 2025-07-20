import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'models/task.dart';
import 'models/message.dart';

final tasksProvider = StreamProvider<List<Task>>((ref) {
  return FirebaseFirestore.instance
      .collection('tasks')
      .orderBy('createdAt', descending: true)
      .snapshots()
      .map((snap) => snap.docs.map((d) => Task.fromDoc(d)).toList());
});

final messagesProvider = StreamProvider.family<List<Message>, String>((
  ref,
  taskId,
) {
  return FirebaseFirestore.instance
      .collection('tasks')
      .doc(taskId)
      .collection('messages')
      .orderBy('createdAt', descending: false)
      .snapshots()
      .map((snap) => snap.docs.map((d) => Message.fromDoc(d)).toList());
});
