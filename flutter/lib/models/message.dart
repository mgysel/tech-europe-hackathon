import 'package:cloud_firestore/cloud_firestore.dart';

class OptionItem {
  final String name;
  final String summary;
  final String? websiteUrl;
  final String? imageUrl;
  final double? estimatedPrice;
  final double? price;
  final String? recordingUrl;
  final bool selected;
  final String? status;
  final int? rank;
  final String? phone;

  OptionItem({
    required this.name,
    required this.summary,
    this.websiteUrl,
    this.imageUrl,
    this.estimatedPrice,
    this.price,
    this.recordingUrl,
    this.selected = false,
    this.status,
    this.rank,
    this.phone,
  });

  // do not change the string key names, they are correct even thought they dont match the json
  factory OptionItem.fromMap(Map<String, dynamic> map) => OptionItem(
    name: map['name'] as String? ?? '',
    summary: map['description'] as String? ?? '',
    websiteUrl: map['url'] as String?,
    imageUrl: map['image_url'] as String?,
    estimatedPrice: (map['estimated_price'] as num?)?.toDouble(),
    price: (map['price'] as num?)?.toDouble(),
    recordingUrl: map['recording_url'] as String?,
    selected: map['selected'] as bool? ?? false,
    rank: map['rank'] as int?,
    status: map['status'] as String?,
    phone: map['phone'] as String?,
  );

  Map<String, dynamic> toMap() => {
    'name': name,
    'description': summary,
    if (websiteUrl != null) 'url': websiteUrl,
    if (imageUrl != null) 'image_url': imageUrl,
    if (estimatedPrice != null) 'estimated_price': estimatedPrice,
    if (price != null) 'price': price,
    if (recordingUrl != null) 'recording_url': recordingUrl,
    if (selected) 'selected': true,
    if (status != null) 'status': status,
    if (rank != null) 'rank': rank,
    if (phone != null) 'phone': phone,
  };
}

class Message {
  final String id;
  final String text;
  final String sender;
  final Timestamp createdAt;
  final List<OptionItem> options;
  final String? recordingUrl;

  Message({
    required this.id,
    required this.text,
    required this.sender,
    required this.createdAt,
    this.options = const [],
    this.recordingUrl,
  });

  factory Message.fromDoc(DocumentSnapshot<Map<String, dynamic>> doc) {
    final data = doc.data() ?? {};
    final opts =
        (data['options'] as List?)
            ?.whereType<Map<String, dynamic>>()
            .map((m) => OptionItem.fromMap(m))
            .toList() ??
        [];
    return Message(
      id: doc.id,
      text: data['text'] as String? ?? '',
      sender: data['sender'] as String? ?? '',
      createdAt: data['createdAt'] as Timestamp? ?? Timestamp.now(),
      options: opts,
      recordingUrl: data['recording_url'] as String?,
    );
  }
}
