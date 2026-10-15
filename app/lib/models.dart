class Seller {
  final String name;
  final int? price;
  final String? city;
  Seller(this.name, this.price, this.city);
  factory Seller.fromJson(Map<String, dynamic> j) =>
      Seller(j['name'] ?? '?', j['price'], j['city']);
}

class Product {
  final Map<String, dynamic> raw;
  Product(this.raw);

  String get source => raw['source'];
  String get sourceId => raw['source_id'];
  String get title => raw['title'] ?? '';
  String get url => raw['url'] ?? '';
  String? get image => raw['image'];
  int? get price => raw['price'];
  int? get oldPrice => raw['old_price'];
  double? get rating => (raw['rating'] as num?)?.toDouble();
  int? get ratingCount => raw['rating_count'];
  int? get soldCount => raw['sold_count'];
  int? get sellerCount => raw['seller_count'];
  double get opportunity => (raw['opportunity_score'] as num).toDouble();
  double get demand => (raw['demand_score'] as num).toDouble();
  Map<String, dynamic> get specs => Map<String, dynamic>.from(raw['specs'] ?? {});
  Map<String, dynamic> get extra => Map<String, dynamic>.from(raw['extra'] ?? {});
  List<Seller> get sellers =>
      ((raw['sellers'] ?? []) as List).map((e) => Seller.fromJson(e)).toList();
}

String fmtNum(num? n) {
  if (n == null) return '—';
  final s = n.round().toString();
  final b = StringBuffer();
  for (var i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 == 0) b.write('٬');
    b.write(s[i]);
  }
  return b.toString();
}
