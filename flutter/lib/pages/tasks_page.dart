import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers.dart';
import 'messages_page.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

String _relativeTime(DateTime date) {
  final diff = DateTime.now().difference(date);
  if (diff.inSeconds < 60) return '${diff.inSeconds}s ago';
  if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
  if (diff.inHours < 24) return '${diff.inHours}h ago';
  if (diff.inDays == 1) return 'Yesterday';
  return '${date.month}/${date.day}/${date.year}';
}

class TasksPage extends ConsumerWidget {
  const TasksPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasksAsync = ref.watch(tasksProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Agent tasks'),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8.0),
            child: ElevatedButton.icon(
              onPressed: () async {
                final instrController = TextEditingController();
                final added = await showDialog<bool>(
                  context: context,
                  barrierDismissible: false,
                  builder: (context) {
                    return AlertDialog(
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      title: const Text('New Task Instruction'),
                      content: SizedBox(
                        width: 400,
                        child: TextField(
                          controller: instrController,
                          autofocus: true,
                          maxLines: 5,
                          decoration: const InputDecoration(
                            hintText: 'Describe the task...',
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context, false),
                          child: const Text('Cancel'),
                        ),
                        ElevatedButton(
                          onPressed: () => Navigator.pop(context, true),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Theme.of(
                              context,
                            ).colorScheme.primary,
                            foregroundColor: Theme.of(
                              context,
                            ).colorScheme.onPrimary,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                          child: const Text('Add'),
                        ),
                      ],
                    );
                  },
                );

                if (added == true && instrController.text.trim().isNotEmpty) {
                  final text = instrController.text.trim();
                  final taskRef = await FirebaseFirestore.instance
                      .collection('tasks')
                      .add({
                        'instruction': text,
                        'createdAt': FieldValue.serverTimestamp(),
                      });
                  await taskRef.collection('messages').add({
                    'text': text,
                    'sender': 'me',
                    'createdAt': FieldValue.serverTimestamp(),
                  });

                  // Notify external endpoint with new task
                  try {
                    await http.post(
                      Uri.parse(
                        'https://tech-europe-hackathon-2025-2dbae1302525.herokuapp.com/order',
                      ),
                      headers: {'Content-Type': 'application/json'},
                      body: jsonEncode({'task_id': taskRef.id}),
                    );
                  } catch (_) {
                    // ignore
                  }
                }
              },
              icon: const Icon(Icons.add),
              label: const Text('Add Task'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Theme.of(context).colorScheme.onPrimary,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
          ),
        ],
      ),
      body: tasksAsync.when(
        data: (tasks) {
          if (tasks.isEmpty) {
            return const Center(
              child: Text('No tasks yet. Tap + to add your first task!'),
            );
          }
          return ListView.builder(
            itemCount: tasks.length,
            itemBuilder: (context, index) {
              final task = tasks[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: ListTile(
                  title: Text(
                    task.instruction.isEmpty ? 'Untitled' : task.instruction,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(_relativeTime(task.createdAt)),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => MessagesPage(task: task),
                      ),
                    );
                  },
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Error: $e')),
      ),
    );
  }
}
