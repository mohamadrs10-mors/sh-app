import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../widgets/product_tile.dart';

class SavedScreen extends StatefulWidget {
  const SavedScreen({super.key});
  @override
  State<SavedScreen> createState() => _SavedScreenState();
}

class _SavedScreenState extends State<SavedScreen> {
  Future<List<Product>> f = Api.saved();
  @override
  Widget build(BuildContext context) => Column(children: [
        Align(alignment: Alignment.centerLeft,
            child: IconButton(icon: const Icon(Icons.refresh),
                onPressed: () => setState(() => f = Api.saved()))),
        Expanded(child: FutureBuilder<List<Product>>(
            future: f,
            builder: (_, s) {
              if (!s.hasData) return const Center(child: CircularProgressIndicator());
              if (s.data!.isEmpty) return const Center(child: Text('هنوز چیزی ذخیره نکرده‌اید (نگه‌داشتن روی محصول)'));
              return ListView(children: [for (final p in s.data!) ProductTile(p)]);
            })),
      ]);
}
