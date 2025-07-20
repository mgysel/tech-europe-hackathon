import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/task.dart';
import '../providers.dart';
import '../models/message.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:audioplayers/audioplayers.dart';
import 'package:url_launcher/url_launcher.dart';

class MessagesPage extends ConsumerWidget {
  final Task task;
  const MessagesPage({super.key, required this.task});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final messagesAsync = ref.watch(messagesProvider(task.id));

    return Scaffold(
      appBar: AppBar(
        centerTitle: false,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            GestureDetector(
              onTap: () {
                Clipboard.setData(ClipboardData(text: task.id));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Task ID copied to clipboard')),
                );
              },
              child: Text(
                task.id,
                style: Theme.of(
                  context,
                ).textTheme.bodySmall?.copyWith(color: Colors.grey.shade600),
              ),
            ),
            Text(
              task.instruction.isEmpty ? 'Task' : task.instruction,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: messagesAsync.when(
              data: (messages) => messages.isEmpty
                  ? const Center(child: Text('No messages yet'))
                  : _MessagesList(messages: messages, taskId: task.id),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, st) => Center(child: Text('Error: $e')),
            ),
          ),
          _MessageInput(taskId: task.id),
        ],
      ),
    );
  }
}

class _MessagesList extends StatelessWidget {
  final List<Message> messages;
  final String taskId;
  const _MessagesList({required this.messages, required this.taskId});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(8),
      itemCount: _displayMessages(messages).length,
      itemBuilder: (context, idx) {
        final msg = _displayMessages(messages)[idx];
        final isMe = msg.sender == 'me';
        return Align(
          alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
          child: msg.options.isNotEmpty
              ? _OptionsBubble(
                  options: msg.options,
                  taskId: taskId,
                  messageId: msg.id,
                )
              : msg.recordingUrl != null
              ? _RecordingBubble(url: msg.recordingUrl!)
              : (msg.sender == 'agent' && msg.text.isEmpty)
              ? const _LoadingBubble()
              : _TextBubble(isMe: isMe, text: msg.text),
        );
      },
    );
  }

  List<Message> _displayMessages(List<Message> messages) {
    final list = [...messages];

    if (!list.any((m) => m.options.isNotEmpty) && false) {
      final dummyOptions = Message(
        id: 'demo',
        text: '',
        sender: 'agent',
        createdAt: Timestamp.now(),
        options: [
          OptionItem(
            name: 'Cool App',
            summary: 'An awesome application that does something great.',
            websiteUrl: 'https://example.com',
            imageUrl: null,
          ),
          OptionItem(
            name: 'Another App',
            summary: 'Makes your life easier by automating tasks.',
            websiteUrl: 'https://example.org',
          ),
        ],
      );
      list.add(dummyOptions);
    }

    if (!list.any((m) => m.recordingUrl != null) && false) {
      list.add(
        Message(
          id: 'demo_rec',
          text: '',
          sender: 'agent',
          createdAt: Timestamp.now(),
          recordingUrl:
              'https://storage.googleapis.com/livekit-egress-synthflow/room-call_0875704225_8b6ff222-4d5e-4849-8550-58f083876416-call-9b875ad6-3d7b-4e89-bf80-aa6505c2decf.mp4?Expires=4906538125&GoogleAccessId=livekit-egress%40synthflow-dev.iam.gserviceaccount.com&Signature=gR%2FvrCCRx6MzFPI2OkBDeiaVNiJm2WsDT2TatZJaXpu1E5xBhYw4Boy%2BOQpCL1ZHh2BXhrNrVD683gclAfswfMdSTv4OJHsaNEyppSJlxbz2QOjKdMBy6RpZgnp5bs%2Bil4NXQe6uaHYWfyj56Hw68sbTSP5umCT3j4oxVF%2FA6gHSUUoBoKsxXeXtOp1BA3zOqgdIynwV6NBKU2aPX3uggbLEOjiuexBjL%2BUFuICD2JTQ%2BL8YTMG96CphvnHZwzFOF%2BBphFUGHcgXzwYN4%2FYclqE4NCOZreLTSVz9KJ%2Fn0%2FJ%2Fiib%2Fsi28SKx8D%2FWiKoVWFG40xU4jGRX7Wct5ZrnU3Q%3D%3D',
        ),
      );
    }

    // append synthetic analyzing bubble if last message from user
    if (list.isNotEmpty && list.last.sender == 'me') {
      list.add(
        Message(
          id: 'local_loading',
          text: '',
          sender: 'agent',
          createdAt: Timestamp.now(),
        ),
      );
    }
    return list;
  }
}

class _TextBubble extends StatelessWidget {
  final bool isMe;
  final String text;
  const _TextBubble({required this.isMe, required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: isMe ? Colors.blueAccent.shade700 : Colors.grey.shade300,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style: TextStyle(color: isMe ? Colors.white : Colors.black),
      ),
    );
  }
}

class _OptionsBubble extends StatefulWidget {
  final List<OptionItem> options;
  final String taskId;
  final String messageId;
  const _OptionsBubble({
    required this.options,
    required this.taskId,
    required this.messageId,
  });

  @override
  State<_OptionsBubble> createState() => _OptionsBubbleState();
}

class _OptionsBubbleState extends State<_OptionsBubble> {
  late List<bool> _selected;

  @override
  void initState() {
    super.initState();
    _selected = List.filled(widget.options.length, false);
  }

  bool get _dbHasSelected => widget.options.any((o) => o.selected);

  Future<void> _confirmOrder(int idxInFull) async {
    final updated = List<Map<String, dynamic>>.from(
      widget.options.map((o) => o.toMap()),
    );
    updated[idxInFull]['status'] = 'confirmed';

    await FirebaseFirestore.instance
        .collection('tasks')
        .doc(widget.taskId)
        .collection('messages')
        .doc(widget.messageId)
        .update({'options': updated});
  }

  @override
  Widget build(BuildContext context) {
    final displayOptions = _dbHasSelected
        ? widget.options.where((o) => o.selected).toList()
        : widget.options;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ...List.generate(displayOptions.length, (idx) {
            final opt = displayOptions[idx];
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 6.0),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(8),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 4,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                padding: const EdgeInsets.all(8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    if (!_dbHasSelected)
                      Checkbox(
                        value: _selected[idx],
                        onChanged: (val) =>
                            setState(() => _selected[idx] = val ?? false),
                      ),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            opt.name,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 4),
                          if (opt.status == 'completed' ||
                              opt.status == 'confirmed') ...[
                            Text(opt.summary),
                            const SizedBox(height: 2),
                            const Text(
                              'Price: €100.00',
                              style: TextStyle(fontWeight: FontWeight.w600),
                            ),
                            const Text('Availability: 3–5 PM'),
                          ] else ...[
                            Text(opt.summary),
                            if (opt.estimatedPrice != null)
                              Padding(
                                padding: const EdgeInsets.only(top: 2.0),
                                child: Text(
                                  'Estimated: €${opt.estimatedPrice!.toStringAsFixed(2)}',
                                  style: const TextStyle(color: Colors.green),
                                ),
                              ),
                            if (opt.price != null)
                              Text(
                                'Price: €${opt.price!.toStringAsFixed(2)}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                          ],

                          if (opt.websiteUrl != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 4.0),
                              child: InkWell(
                                onTap: () async {
                                  final uri = Uri.parse(opt.websiteUrl!);
                                  if (await canLaunchUrl(uri)) {
                                    await launchUrl(
                                      uri,
                                      mode: LaunchMode.externalApplication,
                                    );
                                  }
                                },
                                child: Text(
                                  opt.websiteUrl!,
                                  style: const TextStyle(
                                    color: Colors.blue,
                                    decoration: TextDecoration.underline,
                                  ),
                                ),
                              ),
                            ),
                          if (opt.status == 'loading')
                            Padding(
                              padding: const EdgeInsets.only(top: 4.0),
                              child: Chip(
                                label: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: const [
                                    SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    ),
                                    SizedBox(width: 6),
                                    Text('Call in progress'),
                                  ],
                                ),
                              ),
                            ),
                          if (opt.status == 'completed')
                            Padding(
                              padding: const EdgeInsets.only(top: 4.0),
                              child: Row(
                                children: [
                                  const Chip(
                                    label: Text('Completed'),
                                    backgroundColor: Colors.greenAccent,
                                  ),
                                  const SizedBox(width: 8),
                                  ElevatedButton(
                                    onPressed: () {
                                      final fullIdx = widget.options.indexOf(
                                        opt,
                                      );
                                      _confirmOrder(fullIdx);
                                    },
                                    child: const Text('Confirm order'),
                                  ),
                                ],
                              ),
                            ),
                          if (opt.status == 'confirmed')
                            Padding(
                              padding: const EdgeInsets.only(top: 4.0),
                              child: const Chip(
                                label: Text('Order confirmed'),
                                backgroundColor: Colors.blueAccent,
                              ),
                            ),
                        ],
                      ),
                    ),
                    if (opt.imageUrl != null)
                      Padding(
                        padding: const EdgeInsets.only(right: 8.0),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(6),
                          child: Image.network(
                            opt.imageUrl!,
                            width: 64,
                            height: 64,
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const Icon(
                              Icons.broken_image,
                              size: 40,
                              color: Colors.grey,
                            ),
                          ),
                        ),
                      ),
                    if (opt.recordingUrl != null)
                      SizedBox(
                        width: 200,
                        child: _MiniRecordingBubble(url: opt.recordingUrl!),
                      ),
                  ],
                ),
              ),
            );
          }),
          if (!_dbHasSelected && _selected.any((e) => e))
            Align(
              alignment: Alignment.centerRight,
              child: ElevatedButton(
                onPressed: _requestOffers,
                child: const Text('Request offers'),
              ),
            ),
        ],
      ),
    );
  }

  Future<void> _requestOffers() async {
    final chosen = <OptionItem>[];
    for (var i = 0; i < widget.options.length; i++) {
      if (_selected[i]) chosen.add(widget.options[i]);
    }
    if (chosen.isEmpty) return;

    // build updated options list with selected flag
    final updated = List<Map<String, dynamic>>.from(
      widget.options.map((o) {
        final map = o.toMap();
        return map;
      }),
    );
    for (var i = 0; i < _selected.length && i < updated.length; i++) {
      if (_selected[i]) updated[i]['selected'] = true;
    }

    await FirebaseFirestore.instance
        .collection('tasks')
        .doc(widget.taskId)
        .collection('messages')
        .doc(widget.messageId)
        .update({'options': updated});

    // Notify external endpoint
    try {
      await http.post(
        Uri.parse(
          'https://tech-europe-hackathon-2025-2dbae1302525.herokuapp.com/execute-phone-calls',
        ),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'task_id': widget.taskId}),
      );
    } catch (_) {}

    setState(() => _selected = List.filled(widget.options.length, false));
  }
}

class _RecordingBubble extends StatefulWidget {
  final String url;
  const _RecordingBubble({required this.url});

  @override
  State<_RecordingBubble> createState() => _RecordingBubbleState();
}

class _RecordingBubbleState extends State<_RecordingBubble> {
  late final AudioPlayer _player;
  bool _playing = false;
  Duration _duration = Duration.zero;
  Duration _position = Duration.zero;

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();

    _player.onDurationChanged.listen((d) => setState(() => _duration = d));
    _player.onPositionChanged.listen((p) => setState(() => _position = p));
    _player.onPlayerComplete.listen((_) {
      setState(() {
        _playing = false;
        _position = _duration;
      });
    });
  }

  Future<void> _toggle() async {
    if (_playing) {
      await _player.pause();
      setState(() => _playing = false);
    } else {
      await _player.play(UrlSource(widget.url));
      setState(() => _playing = true);
    }
  }

  String _fmt(Duration d) {
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final progress = _duration.inMilliseconds == 0
        ? 0.0
        : _position.inMilliseconds / _duration.inMilliseconds;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Call Recording',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.start,
            children: [
              IconButton(
                icon: Icon(_playing ? Icons.pause : Icons.play_arrow),
                onPressed: _toggle,
              ),
              Text('${_fmt(_position)} / ${_fmt(_duration)}'),
            ],
          ),
          SizedBox(width: 200, child: LinearProgressIndicator(value: progress)),
        ],
      ),
    );
  }
}

class _MiniRecordingBubble extends StatefulWidget {
  final String url;
  const _MiniRecordingBubble({required this.url});

  @override
  State<_MiniRecordingBubble> createState() => _MiniRecordingBubbleState();
}

class _MiniRecordingBubbleState extends State<_MiniRecordingBubble> {
  late final AudioPlayer _player;
  bool _playing = false;
  Duration _duration = Duration.zero;
  Duration _position = Duration.zero;

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _player.onDurationChanged.listen((d) => setState(() => _duration = d));
    _player.onPositionChanged.listen((p) => setState(() => _position = p));
    _player.onPlayerComplete.listen((_) {
      setState(() {
        _playing = false;
        _position = _duration;
      });
    });
  }

  String _fmt(Duration d) {
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  Future<void> _toggle() async {
    if (_playing) {
      await _player.pause();
      setState(() => _playing = false);
    } else {
      await _player.play(UrlSource(widget.url));
      setState(() => _playing = true);
    }
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final progress = _duration.inMilliseconds == 0
        ? 0.0
        : _position.inMilliseconds / _duration.inMilliseconds;

    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Colors.grey.shade300),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 3,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Call Recording',
            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.start,
            children: [
              IconButton(
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                iconSize: 20,
                icon: Icon(_playing ? Icons.pause : Icons.play_arrow, size: 20),
                onPressed: _toggle,
              ),
              const SizedBox(width: 4),
              Text(
                '${_fmt(_position)} / ${_fmt(_duration)}',
                style: const TextStyle(fontSize: 12),
              ),
            ],
          ),
          LinearProgressIndicator(value: progress, minHeight: 4),
        ],
      ),
    );
  }
}

class _InlineAudioPlayer extends StatefulWidget {
  final String url;
  const _InlineAudioPlayer({required this.url});

  @override
  State<_InlineAudioPlayer> createState() => _InlineAudioPlayerState();
}

class _InlineAudioPlayerState extends State<_InlineAudioPlayer> {
  late final AudioPlayer _player;
  bool _playing = false;

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _player.onPlayerComplete.listen((_) => setState(() => _playing = false));
  }

  Future<void> _toggle() async {
    if (_playing) {
      await _player.pause();
      setState(() => _playing = false);
    } else {
      await _player.play(UrlSource(widget.url));
      setState(() => _playing = true);
    }
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: Icon(_playing ? Icons.pause_circle_filled : Icons.play_circle_fill),
      onPressed: _toggle,
      color: Colors.blueAccent,
      iconSize: 36,
    );
  }
}

class _MessageInput extends StatefulWidget {
  final String taskId;
  const _MessageInput({required this.taskId});

  @override
  State<_MessageInput> createState() => _MessageInputState();
}

class _MessageInputState extends State<_MessageInput> {
  final _controller = TextEditingController();
  bool _sending = false;

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    setState(() => _sending = true);
    final msgRef = await FirebaseFirestore.instance
        .collection('tasks')
        .doc(widget.taskId)
        .collection('messages')
        .add({
          'text': text,
          'sender': 'me',
          'createdAt': FieldValue.serverTimestamp(),
        });

    // Notify external endpoint
    try {
      print('Sending message to external endpoint');
      await http.post(
        Uri.parse(
          'https://tech-europe-hackathon-2025-2dbae1302525.herokuapp.com/order',
        ),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'task_id': widget.taskId}),
      );
    } catch (e) {
      // Silently ignore errors
      print('Error sending message: $e');
    }
    setState(() => _sending = false);
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _send(),
                decoration: const InputDecoration(
                  hintText: 'Type a message...',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: _sending
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send),
              onPressed: _sending ? null : _send,
            ),
          ],
        ),
      ),
    );
  }
}

class _LoadingBubble extends StatelessWidget {
  const _LoadingBubble();

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: const [
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          SizedBox(width: 8),
          Text('Analyzing...'),
        ],
      ),
    );
  }
}
