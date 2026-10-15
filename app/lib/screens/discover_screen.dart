import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../widgets/product_tile.dart';

class DiscoverScreen extends StatefulWidget {
  const DiscoverScreen({super.key});
  @override
  State<DiscoverScreen> createState() => _DiscoverScreenState();
}

class _DiscoverScreenState extends State<DiscoverScreen> {
  final cat = TextEditingController();
  final minP = TextEditingController();
  final maxP = TextEditingController();
  String source = 'digikala';
  String sort = 'bestseller';
  bool loading = false;
  String? error;
  List<Product> items = [];

  Future<void> run() async {
    setState(() { loading = true; error = null; });
    try {
      items = await Api.discover(source, cat.text.trim(), sort,
          minPrice: int.tryParse(minP.text), maxPrice: int.tryParse(maxP.text));
    } catch (e) {
      error = e.toString();
    }
    if (mounted) setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final hint = source == 'digikala'
        ? 'اسلاگ دسته (مثلاً wood-and-timber از آدرس دسته در دیجی‌کالا)'
        : 'عبارت جستجو (مثلاً تخته چوب راش)';
    return Column(children: [
      Padding(
        padding: const EdgeInsets.all(12),
        child: Wrap(spacing: 8, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
          DropdownButton<String>(value: source, onChanged: (v) => setState(() => source = v!),
              items: sourceLabels.entries
                  .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value))).toList()),
          DropdownButton<String>(value: sort, onChanged: (v) => setState(() => sort = v!),
              items: const [
                DropdownMenuItem(value: 'bestseller', child: Text('پرفروش‌ترین')),
                DropdownMenuItem(value: 'visits', child: Text('پربازدیدترین')),
                DropdownMenuItem(value: 'newest', child: Text('جدیدترین')),
                DropdownMenuItem(value: 'cheapest', child: Text('ارزان‌ترین')),
              ]),
          SizedBox(width: 340, child: TextField(controller: cat,
              decoration: InputDecoration(labelText: 'دسته / عبارت', hintText: hint))),
          SizedBox(width: 120, child: TextField(controller: minP, keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'حداقل قیمت'))),
          SizedBox(width: 120, child: TextField(controller: maxP, keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'حداکثر قیمت'))),
          FilledButton.icon(onPressed: loading ? null : run,
              icon: const Icon(Icons.search), label: const Text('بیاب')),
          if (items.isNotEmpty)
            OutlinedButton.icon(
              onPressed: () async {
                final path = await Api.exportCsv(items);
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('ذخیره شد: $path')));
                }
              },
              icon: const Icon(Icons.download), label: const Text('خروجی CSV')),
        ]),
      ),
      if (loading) const LinearProgressIndicator(),
      if (error != null) Padding(padding: const EdgeInsets.all(12),
          child: Text(error!, style: const TextStyle(color: Colors.red))),
      Expanded(child: ListView.builder(
          itemCount: items.length, itemBuilder: (_, i) => ProductTile(items[i]))),
    ]);
  }
}
