import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../widgets/product_tile.dart';

class AnalyzeScreen extends StatefulWidget {
  final String? initialUrl;
  final bool standalone;
  const AnalyzeScreen({super.key, this.initialUrl, this.standalone = false});
  @override
  State<AnalyzeScreen> createState() => _AnalyzeScreenState();
}

class _AnalyzeScreenState extends State<AnalyzeScreen> {
  late final url = TextEditingController(text: widget.initialUrl);
  bool loading = false;
  String? error;
  Product? main;
  List<Product> others = [];
  List history = [];

  @override
  void initState() {
    super.initState();
    if (widget.initialUrl != null) WidgetsBinding.instance.addPostFrameCallback((_) => run());
  }

  Future<void> run() async {
    setState(() { loading = true; error = null; });
    try {
      final r = await Api.analyze(url.text.trim());
      main = r.product; others = r.others; history = r.history;
    } catch (e) {
      error = e.toString();
    }
    if (mounted) setState(() => loading = false);
  }

  Widget kv(String k, Object? v) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(width: 150, child: Text(k, style: const TextStyle(fontWeight: FontWeight.bold))),
        Expanded(child: SelectableText('${v ?? '—'}')),
      ]));

  @override
  Widget build(BuildContext context) {
    final m = main;
    final body = ListView(padding: const EdgeInsets.all(12), children: [
      Row(children: [
        Expanded(child: TextField(controller: url,
            decoration: const InputDecoration(labelText: 'لینک محصول (دیجی‌کالا / ترب / باسلام)'))),
        const SizedBox(width: 8),
        FilledButton(onPressed: loading ? null : run, child: const Text('تحلیل')),
      ]),
      if (loading) const LinearProgressIndicator(),
      if (error != null) Text(error!, style: const TextStyle(color: Colors.red)),
      if (m != null) ...[
        const SizedBox(height: 12),
        Text(m.title, style: Theme.of(context).textTheme.titleLarge),
        kv('منبع', sourceLabels[m.source]),
        kv('قیمت', '${fmtNum(m.price)} تومان'),
        if (m.oldPrice != null) kv('قیمت قبل از تخفیف', fmtNum(m.oldPrice)),
        kv('امتیاز', m.rating),
        kv('تعداد نظرات/امتیاز', fmtNum(m.ratingCount)),
        if (m.soldCount != null) kv('تعداد فروش', fmtNum(m.soldCount)),
        kv('تعداد فروشنده', m.sellerCount),
        kv('امتیاز تقاضا', m.demand),
        kv('امتیاز فرصت', m.opportunity),
        for (final e in m.extra.entries) if (e.value != null) kv(e.key, e.value),
        if (m.specs.isNotEmpty) ...[
          const Divider(), const Text('مشخصات', style: TextStyle(fontWeight: FontWeight.bold)),
          for (final e in m.specs.entries) kv(e.key, e.value),
        ],
        if (m.sellers.isNotEmpty) ...[
          const Divider(), const Text('فروشندگان', style: TextStyle(fontWeight: FontWeight.bold)),
          for (final s in m.sellers) kv(s.name, '${fmtNum(s.price)} تومان ${s.city ?? ''}'),
        ],
        if (history.length > 1) ...[
          const Divider(), const Text('تاریخچه‌ی ثبت‌شده', style: TextStyle(fontWeight: FontWeight.bold)),
          for (final h in history)
            kv(DateTime.fromMillisecondsSinceEpoch((h['ts'] * 1000).round()).toString().substring(0, 16),
                'قیمت ${fmtNum(h['price'])} • نظرات ${fmtNum(h['rating_count'])}'),
        ],
        Row(children: [
          TextButton.icon(onPressed: () => openUrl(m.url), icon: const Icon(Icons.open_in_new),
              label: const Text('باز کردن در سایت')),
          TextButton.icon(onPressed: () => Api.save(m, true), icon: const Icon(Icons.bookmark_add),
              label: const Text('ذخیره')),
        ]),
        if (others.isNotEmpty) ...[
          const Divider(),
          const Text('محصولات مشابه در سایت‌های دیگر', style: TextStyle(fontWeight: FontWeight.bold)),
          for (final o in others) ProductTile(o),
        ],
      ],
    ]);
    return widget.standalone ? Scaffold(appBar: AppBar(), body: body) : body;
  }
}
