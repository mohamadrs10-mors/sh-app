import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api.dart';
import '../models.dart';
import '../screens/analyze_screen.dart';

const sourceLabels = {'digikala': 'دیجی‌کالا', 'torob': 'ترب', 'basalam': 'باسلام'};

class ProductTile extends StatelessWidget {
  final Product p;
  final bool compact;
  const ProductTile(this.p, {super.key, this.compact = false});

  @override
  Widget build(BuildContext context) {
    final demandLabel = p.soldCount != null
        ? 'فروش: ${fmtNum(p.soldCount)}'
        : 'نظرات: ${fmtNum(p.ratingCount)}';
    return Card(
      child: ListTile(
        leading: p.image == null
            ? const Icon(Icons.inventory_2)
            : Image.network(p.image!, width: 56, height: 56, fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const Icon(Icons.inventory_2)),
        title: Text(p.title, maxLines: 2, overflow: TextOverflow.ellipsis),
        subtitle: Text('${sourceLabels[p.source] ?? p.source} • ${fmtNum(p.price)} تومان\n'
            '$demandLabel • فروشنده: ${fmtNum(p.sellerCount)} • امتیاز: ${p.rating ?? '—'}'),
        isThreeLine: true,
        trailing: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Text(p.opportunity.toStringAsFixed(0),
              style: Theme.of(context).textTheme.headlineSmall),
          const Text('فرصت', style: TextStyle(fontSize: 10)),
        ]),
        onTap: () => Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => AnalyzeScreen(initialUrl: p.url, standalone: true))),
        onLongPress: () async {
          await Api.save(p, true);
          if (context.mounted) {
            ScaffoldMessenger.of(context)
                .showSnackBar(const SnackBar(content: Text('ذخیره شد')));
          }
        },
      ),
    );
  }
}

Future<void> openUrl(String url) => launchUrl(Uri.parse(url));
