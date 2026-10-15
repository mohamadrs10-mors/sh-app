import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;
import 'package:shared_preferences/shared_preferences.dart';

import 'models.dart';

/// در ویندوز، بک‌اند پایتون همراه برنامه اجرا می‌شود؛ در موبایل آدرس سرور
/// (کامپیوتر ویندوزی که برنامه روی آن باز است) در تنظیمات وارد می‌شود.
class Api {
  static String baseUrl = 'http://127.0.0.1:8765';
  static Process? _proc;

  static bool get isDesktop => Platform.isWindows;

  static Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    if (isDesktop) {
      await _startLocalBackend();
      // اجازه بده موبایل‌های شبکه‌ی محلی هم وصل شوند: --host 0.0.0.0
    } else {
      baseUrl = prefs.getString('server') ?? 'http://192.168.1.10:8765';
    }
  }

  static Future<void> setServer(String url) async {
    baseUrl = url;
    (await SharedPreferences.getInstance()).setString('server', url);
  }

  static Future<void> _startLocalBackend() async {
    if (await _healthy()) return;
    final dir = p.dirname(Platform.resolvedExecutable);
    final exe = p.join(dir, 'backend', 'backend.exe');
    if (!File(exe).existsSync()) return; // حالت توسعه: دستی python run.py
    final share = (await SharedPreferences.getInstance()).getBool('share_lan') ?? false;
    _proc = await Process.start(exe, ['--host', share ? '0.0.0.0' : '127.0.0.1']);
    for (var i = 0; i < 30 && !await _healthy(); i++) {
      await Future.delayed(const Duration(milliseconds: 300));
    }
  }

  static Future<bool> _healthy() async {
    try {
      final r = await http.get(Uri.parse('$baseUrl/health')).timeout(const Duration(seconds: 1));
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static void dispose() => _proc?.kill();

  static Future<dynamic> _post(String path, Map body) async {
    final r = await http
        .post(Uri.parse('$baseUrl$path'),
            headers: {'Content-Type': 'application/json'}, body: jsonEncode(body))
        .timeout(const Duration(seconds: 120));
    final data = jsonDecode(utf8.decode(r.bodyBytes));
    if (r.statusCode != 200) throw Exception(data['detail'] ?? 'خطا ${r.statusCode}');
    return data;
  }

  static Future<List<Product>> discover(String source, String category, String sort,
      {int pages = 2, int? minPrice, int? maxPrice}) async {
    final d = await _post('/api/discover', {
      'source': source, 'category': category, 'sort': sort, 'pages': pages,
      'min_price': minPrice, 'max_price': maxPrice,
    });
    return (d as List).map((e) => Product(e)).toList();
  }

  static Future<({Product product, List<Product> others, List history})> analyze(
      String url) async {
    final d = await _post('/api/analyze', {'url': url});
    return (
      product: Product(d['product']),
      others: (d['other_sites'] as List).map((e) => Product(e)).toList(),
      history: d['history'] as List,
    );
  }

  static Future<void> save(Product pr, bool saved) async {
    await http.post(Uri.parse('$baseUrl/api/save/${pr.source}/${pr.sourceId}?saved=$saved'));
  }

  static Future<List<Product>> saved() async {
    final r = await http.get(Uri.parse('$baseUrl/api/saved'));
    return (jsonDecode(utf8.decode(r.bodyBytes)) as List).map((e) => Product(e)).toList();
  }

  static Future<String> exportCsv(List<Product> items) async {
    final r = await http.post(Uri.parse('$baseUrl/api/export.csv'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(items.map((e) => e.raw).toList()));
    final f = File(p.join(Directory.systemTemp.path, 'products.csv'));
    await f.writeAsBytes(r.bodyBytes);
    return f.path;
  }
}
