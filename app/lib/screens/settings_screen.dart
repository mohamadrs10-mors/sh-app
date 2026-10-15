import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final server = TextEditingController(text: Api.baseUrl);
  bool share = false;

  @override
  void initState() {
    super.initState();
    SharedPreferences.getInstance().then((p) => setState(() => share = p.getBool('share_lan') ?? false));
  }

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
        if (Api.isDesktop) ...[
          const Text('نسخه‌ی ویندوز خودش سرور است و نیازی به اتصال به جای دیگر ندارد.'),
          SwitchListTile(
            title: const Text('اجازه‌ی اتصال موبایل از شبکه‌ی محلی (بعد از تغییر، برنامه را ببندید و باز کنید)'),
            value: share,
            onChanged: (v) async {
              (await SharedPreferences.getInstance()).setBool('share_lan', v);
              setState(() => share = v);
            }),
        ] else ...[
          const Text('آدرس سرور: کامپیوتر ویندوزی که برنامه روی آن باز است، مثل http://192.168.1.10:8765'),
          TextField(controller: server, decoration: const InputDecoration(labelText: 'آدرس سرور')),
          const SizedBox(height: 8),
          FilledButton(onPressed: () => Api.setServer(server.text.trim()), child: const Text('ذخیره')),
        ],
      ]);
}
