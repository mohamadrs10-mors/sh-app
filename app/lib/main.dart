import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'api.dart';
import 'screens/analyze_screen.dart';
import 'screens/discover_screen.dart';
import 'screens/saved_screen.dart';
import 'screens/settings_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Api.init();
  runApp(const ShApp());
}

class ShApp extends StatelessWidget {
  const ShApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'یابنده‌ی محصول',
        debugShowCheckedModeBanner: false,
        locale: const Locale('fa'),
        supportedLocales: const [Locale('fa')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: ThemeData(colorSchemeSeed: const Color(0xFF8D5524), useMaterial3: true),
        home: const Home(),
      );
}

class Home extends StatefulWidget {
  const Home({super.key});
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  int i = 0;
  @override
  Widget build(BuildContext context) {
    const pages = [DiscoverScreen(), AnalyzeScreen(), SavedScreen(), SettingsScreen()];
    return Scaffold(
      body: SafeArea(child: IndexedStack(index: i, children: pages)),
      bottomNavigationBar: NavigationBar(
        selectedIndex: i,
        onDestinationSelected: (v) => setState(() => i = v),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.trending_up), label: 'کشف پرفروش‌ها'),
          NavigationDestination(icon: Icon(Icons.link), label: 'تحلیل لینک'),
          NavigationDestination(icon: Icon(Icons.bookmark), label: 'ذخیره‌شده'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'تنظیمات'),
        ],
      ),
    );
  }
}
