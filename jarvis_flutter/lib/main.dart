import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'constants.dart';
import 'ui/hud_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Set dark Stark status bar styling
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: StarkConstants.bgDark,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  runApp(const JarvisFlutterApp());
}

class JarvisFlutterApp extends StatelessWidget {
  const JarvisFlutterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: StarkConstants.appName,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: StarkConstants.bgDark,
        colorScheme: const ColorScheme.dark(
          primary: StarkConstants.primaryCyan,
          secondary: StarkConstants.starkRed,
          surface: StarkConstants.panelBg,
        ),
      ),
      home: const HudScreen(),
    );
  }
}
