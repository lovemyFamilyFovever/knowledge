---
title: "Flutter跨平台开发实战"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Flutter跨平台开发实战

# Flutter跨平台开发实战指南

## 1. Dart语言精要

### 1.1 基础语法特性

Dart是一种面向对象的、类定义的、单继承的语言，但支持mixin多继承和接口实现。作为Flutter的基石，Dart的语法设计直接影响了开发体验。

```dart
// 空安全 (Null Safety) - Flutter 2.0+的核心特性
void nullSafetyExample() {
  // 非空类型，必须初始化
  String name = 'Flutter';
  
  // 可空类型
  String? maybeName = null;
  
  // 空安全操作符
  int? length = maybeName?.length;  // 安全访问
  print(length ?? 0);               // 空合并运算符
  
  // 类型提升
  if (maybeName != null) {
    // 这里maybeName自动提升为非空类型
    print(maybeName.length);
  }
  
  // late关键字 - 延迟初始化
  late String description;
  description = '延迟初始化的变量';  // 在使用前必须初始化
}
```

### 1.2 异步编程模型

Dart的异步模型基于事件循环和Future/Stream，这对Flutter开发至关重要。

```dart
import 'dart:async';
import 'dart:convert';
import 'dart:isolate';

// Future的使用
Future<User> fetchUser(String id) async {
  try {
    final response = await http.get('https://api.example.com/users/$id');
    return User.fromJson(json.decode(response.body));
  } catch (e) {
    throw Exception('Failed to load user: $e');
  }
}

// Stream的使用
Stream<int> numberStream() async* {
  for (int i = 0; i < 10; i++) {
    await Future.delayed(Duration(seconds: 1));
    yield i;
  }
}

// Isolate的使用 - 处理CPU密集型任务
Future<dynamic> computeInIsolate(List<dynamic> args) async {
  final receivePort = ReceivePort();
  await Isolate.spawn(_heavyComputation, [sendPort, args]);
  return receivePort.first;
}

void _heavyComputation(List<dynamic> args) {
  final sendPort = args[0] as SendPort;
  final data = args[1];
  // 执行复杂的计算...
  sendPort.send(result);
}

// 使用compute函数简化Isolate调用
Future<List<String>> processLargeData(List<String> data) async {
  return await compute(_processDataInIsolate, data);
}
```

### 1.3 函数式编程特性

Dart支持高阶函数、lambda表达式和集合操作，使代码更简洁。

```dart
// 高阶函数
typedef IntFunction = int Function(int);

List<int> transformNumbers(List<int> numbers, IntFunction transformer) {
  return numbers.map(transformer).toList();
}

// 使用示例
final doubled = transformNumbers([1, 2, 3], (n) => n * 2);
final filtered = [1, 2, 3, 4, 5]
    .where((n) => n.isEven)
    .map((n) => n * 3)
    .reduce((a, b) => a + b);

// 扩展方法 (Extension Methods)
extension StringExtensions on String {
  String capitalize() {
    return '${this[0].toUpperCase()}${substring(1)}';
  }
  
  bool get isPalindrome {
    final reversed = split('').reversed.join();
    return this == reversed;
  }
}

// 使用
print('hello'.capitalize()); // "Hello"
print('radar'.isPalindrome); // true
```

### 1.4 Mixin与抽象类

```dart
// Mixin定义
mixin Loggable {
  void log(String message) {
    print('[$runtimeType] $message');
  }
}

mixin Serializable {
  Map<String, dynamic> toJson();
}

// 抽象类
abstract class BaseEntity with Loggable, Serializable {
  final String id;
  final DateTime createdAt;
  
  BaseEntity(this.id) : createdAt = DateTime.now();
  
  @override
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'createdAt': createdAt.toIso8601String(),
    };
  }
}

// 接口实现
class User extends BaseEntity implements Comparable<User> {
  final String name;
  final String email;
  
  User(super.id, this.name, this.email);
  
  @override
  int compareTo(User other) => name.compareTo(other.name);
  
  @override
  Map<String, dynamic> toJson() {
    return {
      ...super.toJson(),
      'name': name,
      'email': email,
    };
  }
}
```

## 2. Widget体系详解

### 2.1 StatelessWidget vs StatefulWidget

```dart
// StatelessWidget - 无状态组件
class ProfileCard extends StatelessWidget {
  final User user;
  final VoidCallback? onTap;
  
  const ProfileCard({
    required this.user,
    this.onTap,
    Key? key,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          child: Text(user.name[0]),
        ),
        title: Text(user.name),
        subtitle: Text(user.email),
        onTap: onTap,
      ),
    );
  }
}

// StatefulWidget - 有状态组件
class LikeButton extends StatefulWidget {
  final int initialCount;
  final bool isLiked;
  
  const LikeButton({
    this.initialCount = 0,
    this.isLiked = false,
    Key? key,
  }) : super(key: key);
  
  @override
  State<LikeButton> createState() => _LikeButtonState();
}

class _LikeButtonState extends State<LikeButton> 
    with SingleTickerProviderStateMixin {
  late int _likeCount;
  late bool _isLiked;
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  
  @override
  void initState() {
    super.initState();
    _likeCount = widget.initialCount;
    _isLiked = widget.isLiked;
    
    _controller = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
    
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.5)
        .animate(CurvedAnimation(
          parent: _controller,
          curve: Curves.easeInOut,
        ));
  }
  
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
  
  void _toggleLike() {
    setState(() {
      _isLiked = !_isLiked;
      _likeCount += _isLiked ? 1 : -1;
    });
    
    _controller.forward().then((_) {
      _controller.reverse();
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _toggleLike,
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              _isLiked ? Icons.favorite : Icons.favorite_border,
              color: _isLiked ? Colors.red : Colors.grey,
            ),
            const SizedBox(width: 4),
            Text('$_likeCount'),
          ],
        ),
      ),
    );
  }
}
```

### 2.2 InheritedWidget 机制

```dart
// 自定义InheritedWidget
class ThemeDataInherited extends InheritedWidget {
  final ThemeData themeData;
  final VoidCallback toggleTheme;
  
  const ThemeDataInherited({
    required this.themeData,
    required this.toggleTheme,
    required Widget child,
    Key? key,
  }) : super(child: child, key: key);
  
  static ThemeDataInherited of(BuildContext context) {
    final ThemeDataInherited? result = 
        context.dependOnInheritedWidgetOfExactType<ThemeDataInherited>();
    assert(result != null, 'No ThemeColors found in context');
    return result!;
  }
  
  @override
  bool updateShouldNotify(ThemeDataInherited oldWidget) {
    return themeData != oldWidget.themeData;
  }
}

// 使用InheritedWidget
class AppThemeWrapper extends StatefulWidget {
  final Widget child;
  
  const AppThemeWrapper({required this.child, Key? key}) : super(key: key);
  
  @override
  State<AppThemeWrapper> createState() => _AppThemeWrapperState();
}

class _AppThemeWrapperState extends State<AppThemeWrapper> {
  bool isDarkMode = false;
  
  void _toggleTheme() {
    setState(() {
      isDarkMode = !isDarkMode;
    });
  }
  
  @override
  Widget build(BuildContext context) {
    final themeData = isDarkMode 
        ? ThemeData.dark()
        : ThemeData.light();
    
    return ThemeDataInherited(
      themeData: themeData,
      toggleTheme: _toggleTheme,
      child: Theme(
        data: themeData,
        child: widget.child,
      ),
    );
  }
}

// 在子组件中使用
class ThemedWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = ThemeDataInherited.of(context);
    
    return Column(
      children: [
        Text(
          '当前主题: ${theme.themeData.brightness == Brightness.dark ? "深色" : "浅色"}',
          style: TextStyle(
            color: theme.themeData.primaryColor,
          ),
        ),
        ElevatedButton(
          onPressed: theme.toggleTheme,
          child: const Text('切换主题'),
        ),
      ],
    );
  }
}
```

### 2.3 Provider 状态管理

```dart
// 状态类
class UserState extends ChangeNotifier {
  User? _user;
  bool _isLoading = false;
  String? _error;
  
  User? get user => _user;
  bool get isLoading => _isLoading;
  String? get error => _error;
  
  Future<void> loadUser(String userId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final repository = UserRepository();
      _user = await repository.fetchUser(userId);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  void logout() {
    _user = null;
    notifyListeners();
  }
}

// 在main.dart中配置Provider
void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => UserState()),
        ChangeNotifierProvider(create: (_) => ThemeState()),
        ProxyProvider<UserState, AuthService>(
          update: (_, userState, __) => AuthService(userState),
        ),
      ],
      child: const MyApp(),
    ),
  );
}

// 在Widget中使用Provider
class UserProfileScreen extends StatelessWidget {
  const UserProfileScreen({Key? key}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    // 使用Consumer监听状态变化
    return Consumer<UserState>(
      builder: (context, userState, child) {
        if (userState.isLoading) {
          return const Center(child: CircularProgressIndicator());
        }
        
        if (userState.error != null) {
          return Center(child: Text('错误: ${userState.error}'));
        }
        
        if (userState.user == null) {
          return const LoginScreen();
        }
        
        return UserProfile(user: userState.user!);
      },
    );
  }
}

// 使用Selector优化性能
class LikeCountDisplay extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // 只监听likeCount的变化，避免不必要的重建
    final likeCount = context.select<UserState, int>(
      (userState) => userState.user?.likeCount ?? 0,
    );
    
    return Text('点赞数: $likeCount');
  }
}
```

## 3. 布局系统深入

### 3.1 Flex布局（Row/Column）

```dart
// 复杂登录表单布局
class LoginForm extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Logo部分
          const FlutterLogo(size: 100),
          const SizedBox(height: 32),
          
          // 标题
          const Text(
            '欢迎回来',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          
          // 邮箱输入框
          TextFormField(
            decoration: InputDecoration(
              labelText: '邮箱',
              prefixIcon: const Icon(Icons.email),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            keyboardType: TextInputType.emailAddress,
          ),
          const SizedBox(height: 16),
          
          // 密码输入框
          TextFormField(
            decoration: InputDecoration(
              labelText: '密码',
              prefixIcon: const Icon(Icons.lock),
              suffixIcon: IconButton(
                icon: const Icon(Icons.visibility),
                onPressed: () {},
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            obscureText: true,
          ),
          const SizedBox(height: 8),
          
          // 忘记密码链接
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: () {},
              child: const Text('忘记密码?'),
            ),
          ),
          const SizedBox(height: 24),
          
          // 登录按钮
          ElevatedButton(
            onPressed: () {},
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            child: const Text('登录', style: TextStyle(fontSize: 16)),
          ),
          const SizedBox(height: 16),
          
          // 或者分割线
          Row(
            children: [
              const Expanded(child: Divider()),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text('或者', style: TextStyle(color: Colors.grey[600])),
              ),
              const Expanded(child: Divider()),
            ],
          ),
          const SizedBox(height: 16),
          
          // 社交登录按钮
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SocialLoginButton(
                icon: Icons.g_mobiledata,
                onPressed: () {},
              ),
              const SizedBox(width: 16),
              SocialLoginButton(
                icon: Icons.apple,
                onPressed: () {},
              ),
              const SizedBox(width: 16),
              SocialLoginButton(
                icon: Icons.facebook,
                onPressed: () {},
              ),
            ],
          ),
          const SizedBox(height: 32),
          
          // 注册链接
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('还没有账号?'),
              TextButton(
                onPressed: () {},
                child: const Text('立即注册'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// 自定义响应式布局
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget? desktop;
  
  const ResponsiveLayout({
    required this.mobile,
    this.tablet,
    this.desktop,
    Key? key,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 1200) {
          return desktop ?? tablet ?? mobile;
        } else if (constraints.maxWidth >= 600) {
          return tablet ?? mobile;
        } else {
          return mobile;
        }
      },
    );
  }
}
```

### 3.2 Stack与定位布局

```dart
// 渐变背景的欢迎页
class WelcomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          // 背景渐变
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.deepPurple,
                  Colors.purpleAccent,
                ],
              ),
            ),
          ),
          
          // 背景图片
          Opacity(
            opacity: 0.2,
            child: Image.asset(
              'assets/images/background_pattern.png',
              fit: BoxFit.cover,
            ),
          ),
          
          // 主要内容
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(32.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // 浮动Logo动画
                  const FloatingLogo(),
                  const SizedBox(height: 48),
                  
                  // 标题
                  const Text(
                    '探索世界',
                    style: TextStyle(
                      fontSize: 36,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // 副标题
                  const Text(
                    '连接全球用户，分享精彩生活',
                    style: TextStyle(
                      fontSize: 18,
                      color: Colors.white70,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 64),
                  
                  // 开始按钮
                  ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.deepPurple,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 48,
                        vertical: 16,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(30),
                      ),
                    ),
                    child: const Text(
                      '开始探索',
                      style: TextStyle(fontSize: 18),
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          // 底部装饰
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: ClipPath(
              clipper: WaveClipper(),
              child: Container(
                height: 100,
                color: Colors.white.withOpacity(0.1),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// 自定义Clipper
class WaveClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    final path = Path();
    path.moveTo(0, size.height * 0.7);
    
    final firstControlPoint = Offset(size.width * 0.25, size.height * 0.5);
    final firstEndPoint = Offset(size.width * 0.5, size.height * 0.6);
    path.quadraticBezierTo(
      firstControlPoint.dx,
      firstControlPoint.dy,
      firstEndPoint.dx,
      firstEndPoint.dy,
    );
    
    final secondControlPoint = Offset(size.width * 0.75, size.height * 0.7);
    final secondEndPoint = Offset(size.width, size.height * 0.5);
    path.quadraticBezierTo(
      secondControlPoint.dx,
      secondControlPoint.dy,
      secondEndPoint.dx,
      secondEndPoint.dy,
    );
    
    path.lineTo(size.width, size.height);
    path.lineTo(0, size.height);
    path.close();
    
    return path;
  }
  
  @override
  bool shouldReclip(CustomClipper<Path> oldClipper) => false;
}
```

### 3.3 GridView 网格布局

```dart
// 响应式网格布局
class PhotoGrid extends StatelessWidget {
  final List<Photo> photos;
  
  const PhotoGrid({required this.photos, Key? key}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // 根据屏幕宽度确定列数
        final crossAxisCount = constraints.maxWidth > 1200
            ? 4
            : constraints.maxWidth > 800
                ? 3
                : constraints.maxWidth > 400
                    ? 2
                    : 1;
        
        return GridView.builder(
          padding: const EdgeInsets.all(8),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount,
            childAspectRatio: 1,
            crossAxisSpacing: 8,
            mainAxisSpacing: 8,
          ),
          itemCount: photos.length,
          itemBuilder: (context, index) {
            return PhotoCard(photo: photos[index]);
          },
        );
      },
    );
  }
}

// 瀑布流布局
class MasonryLayout extends StatelessWidget {
  final List<Widget> children;
  final int columnCount;
  
  const MasonryLayout({
    required this.children,
    this.columnCount = 2,
    Key? key,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    // 计算每列的内容
    final columns = List.generate(columnCount, (_) => <Widget>[]);
    
    for (int i = 0; i < children.length; i++) {
      columns[i % columnCount].add(children[i]);
    }
    
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: columns.map((column) {
        return Expanded(
          child: Column(
            children: column,
          ),
        );
      }).toList(),
    );
  }
}
```

## 4. 路由管理（GoRouter）

### 4.1 基础路由配置

```dart
// main.dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

final _router = GoRouter(
  initialLocation: '/',
  debugLogDiagnostics: true,
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
      routes: [
        GoRoute(
          path: 'profile/:userId',
          builder: (context, state) {
            final userId = state.pathParameters['userId']!;
            return ProfileScreen(userId: userId);
          },
        ),
        GoRoute(
          path: 'post/:postId',
          builder: (context, state) {
            final postId = state.pathParameters['postId']!;
            return PostDetailScreen(postId: postId);
          },
        ),
        GoRoute(
          path: 'settings',
          builder: (context, state) => const SettingsScreen(),
          routes: [
            GoRoute(
              path: 'account',
              builder: (context, state) => const AccountSettingsScreen(),
            ),
            GoRoute(
              path: 'privacy',
              builder: (context, state) => const PrivacySettingsScreen(),
            ),
          ],
        ),
      ],
    ),
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/register',
      builder: (context, state) => const RegisterScreen(),
    ),
    // Shell路由（带底部导航栏）
    ShellRoute(
      builder: (context, state, child) {
        return MainShell(child: child);
      },
      routes: [
        GoRoute(
          path: '/home',
          builder: (context, state) => const HomeScreen(),
        ),
        GoRoute(
          path: '/explore',
          builder: (context, state) => const ExploreScreen(),
        ),
        GoRoute(
          path: '/notifications',
          builder: (context, state) => const NotificationsScreen(),
        ),
        GoRoute(
          path: '/profile',
          builder: (context, state) => const ProfileScreen(),
        ),
      ],
    ),
  ],
  redirect: (context, state) {
    final authState = context.read<AuthState>();
    final isLoggedIn = authState.isLoggedIn;
    final isLoginRoute = state.matchedLocation == '/login';
    final isRegisterRoute = state.matchedLocation == '/register';
    
    // 如果未登录且不在登录/注册页面，重定向到登录页
    if (!isLoggedIn && !isLoginRoute && !isRegisterRoute) {
      return '/login';
    }
    
    // 如果已登录且在登录/注册页面，重定向到首页
    if (isLoggedIn && (isLoginRoute || isRegisterRoute)) {
      return '/home';
    }
    
    return null; // 不重定向
  },
  errorBuilder: (context, state) => ErrorScreen(error: state.error),
);

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthState()),
        // ...其他Provider
      ],
      child: MaterialApp.router(
        routerConfig: _router,
        title: '社交媒体App',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          useMaterial3: true,
        ),
      ),
    ),
  );
}

// 主外壳（带底部导航栏）
class MainShell extends StatelessWidget {
  final Widget child;
  
  const MainShell({required this.child, Key? key}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _calculateSelectedIndex(context),
        onTap: (index) => _onItemTapped(index, context),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: '首页',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.explore),
            label: '发现',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.notifications),
            label: '通知',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: '我的',
          ),
        ],
      ),
    );
  }
  
  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location.startsWith('/home')) return 0;
    if (location.startsWith('/explore')) return 1;
    if (location.startsWith('/notifications')) return 2;
    if (location.startsWith('/profile')) return 3;
    return 0;
  }
  
  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        context.go('/home');
        break;
      case 1:
        context.go('/explore');
        break;
      case 2:
        context.go('/notifications');
        break;
      case 3:
        context.go('/profile');
        break;
    }
  }
}
```

### 4.2 高级路由功能

```dart
// 路由守卫和权限控制
class AuthGuard {
  static String? checkAuth(BuildContext context, GoRouterState state) {
    final authState = context.read<AuthState>();
    
    if (!authState.isLoggedIn) {
      // 保存原始URL，登录后重定向
      final from = state.matchedLocation;
      return '/login?from=$from';
    }
    
    // 检查特定路由的权限
    if (state.matchedLocation.startsWith('/admin') && 
        !authState.isAdmin) {
      return '/unauthorized';
    }
    
    return null;
  }
}

// 路由扩展
extension GoRouterExtension on GoRouter {
  void pushWithTransition(
    BuildContext context,
    String location, {
    Object? extra,
  }) {
    push(location, extra: extra);
  }
  
  void goWithTransition(
    BuildContext context,
    String location, {
    Object? extra,
  }) {
    go(location, extra: extra);
  }
  
  void showBottomSheet(
    BuildContext context,
    String location, {
    Object? extra,
  }) {
    showModalBottomSheet(
      context: context,
      builder: (context) => RouterOutlet(
        router: this,
        location: location,
      ),
    );
  }
}

// 命名路由生成器（代码生成）
// 在实际项目中可以使用go_router_builder或auto_route
// 这里展示手动实现
class Routes {
  static const home = '/';
  static const profile = '/profile/:userId';
  static const post = '/post/:postId';
  static const settings = '/settings';
  static const login = '/login';
  
  static String profilePath(String userId) => '/profile/$userId';
  static String postPath(String postId) => '/post/$postId';
}

// 使用命名路由
class SomeWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () {
        context.go(Routes.profilePath('user123'));
      },
      child: const Text('查看个人资料'),
    );
  }
}

// 路由动画自定义
GoRoute(
  path: 'animated-page',
  pageBuilder: (context, state) {
    return CustomTransitionPage(
      child: const AnimatedPage(),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return FadeTransition(
          opacity: animation,
          child: child,
        );
      },
      transitionDuration: const Duration(milliseconds: 300),
    );
  },
)
```

## 5. 状态管理进阶

### 5.1 Riverpod 状态管理

```dart
// 1. 创建Provider
final counterProvider = StateNotifierProvider<CounterNotifier, int>((ref) {
  return CounterNotifier();
});

final userProvider = FutureProvider.family<User, String>((ref, userId) async {
  final userRepository = ref.read(userRepositoryProvider);
  return userRepository.fetchUser(userId);
});

final postsProvider = StreamProvider<List<Post>>((ref) {
  final postRepository = ref.read(postRepositoryProvider);
  return postRepository.watchPosts();
});

// 2. 状态通知器
class CounterNotifier extends StateNotifier<int> {
  CounterNotifier() : super(0);
  
  void increment() => state++;
  void decrement() => state--;
  void reset() => state = 0;
}

// 3. 异步状态管理
final authProvider = StateNotifierProvider<AuthNotifier, AsyncValue<User?>>((ref) {
  return AuthNotifier(ref);
});

class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final Ref ref;
  
  AuthNotifier(this.ref) : super(const AsyncValue.data(null));
  
  Future<void> login(String email, String password) async {
    state = const AsyncValue.loading();
    
    try {
      final authService = ref.read(authServiceProvider);
      final user = await authService.login(email, password);
      state = AsyncValue.data(user);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }
  
  Future<void> logout() async {
    state = const AsyncValue.loading();
    try {
      final authService = ref.read(authServiceProvider);
      await authService.logout();
      state = const AsyncValue.data(null);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }
}

// 4. 组合Provider
final filteredPostsProvider = Provider<AsyncValue<List<Post>>>((ref) {
  final postsAsync = ref.watch(postsProvider);
  final searchQuery = ref.watch(searchQueryProvider);
  final selectedCategory = ref.watch(selectedCategoryProvider);
  
  return postsAsync.whenData((posts) {
    return posts.where((post) {
      final matchesSearch = searchQuery.isEmpty || 
          post.content.contains(searchQuery);
      final matchesCategory = selectedCategory == null || 
          post.category == selectedCategory;
      return matchesSearch && matchesCategory;
    }).toList();
  });
});

// 5. 使用ConsumerWidget
class CounterScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final counter = ref.watch(counterProvider);
    final userAsync = ref.watch(userProvider('user123'));
    
    return Scaffold(
      appBar: AppBar(title: const Text('Riverpod示例')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('计数: $counter', style: const TextStyle(fontSize: 24)),
            const SizedBox(height: 20),
            userAsync.when(
              data: (user) => Text('用户: ${user.name}'),
              loading: () => const CircularProgressIndicator(),
              error: (error, stack) => Text('错误: $error'),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => ref.read(counterProvider.notifier).increment(),
        child: const Icon(Icons.add),
      ),
    );
  }
}

// 6. 自动Dispose
final timerProvider = Provider.autoDispose<Timer>((ref) {
  final timer = Timer.periodic(const Duration(seconds: 1), (timer) {
    print('Timer tick: ${timer.tick}');
  });
  
  ref.onDispose(() {
    timer.cancel();
    print('Timer disposed');
  });
  
  return timer;
});
```

### 5.2 Bloc 状态管理

```dart
// 1. Events
abstract class PostEvent extends Equatable {
  const PostEvent();
  
  @override
  List<Object> get props => [];
}

class LoadPosts extends PostEvent {}
class RefreshPosts extends PostEvent {}
class CreatePost extends PostEvent {
  final String content;
  final List<String> imageUrls;
  
  const CreatePost({required this.content, this.imageUrls = const []});
  
  @override
  List<Object> get props => [content, imageUrls];
}
class LikePost extends PostEvent {
  final String postId;
  
  const LikePost(this.postId);
  
  @override
  List<Object> get props => [postId];
}

// 2. States
abstract class PostState extends Equatable {
  const PostState();
  
  @override
  List<Object> get props => [];
}

class PostInitial extends PostState {}
class PostLoading extends PostState {}
class PostsLoaded extends PostState {
  final List<Post> posts;
  final bool hasReachedMax;
  
  const PostsLoaded({
    required this.posts,
    this.hasReachedMax = false,
  });
  
  PostsLoaded copyWith({
    List<Post>? posts,
    bool? hasReachedMax,
  }) {
    return PostsLoaded(
      posts: posts ?? this.posts,
      hasReachedMax: hasReachedMax ?? this.hasReachedMax,
    );
  }
  
  @override
  List<Object> get props => [posts, hasReachedMax];
}
class PostError extends PostState {
  final String message;
  
  const PostError(this.message);
  
  @override
  List<Object> get props => [message];
}

// 3. Bloc实现
class PostBloc extends Bloc<PostEvent, PostState> {
  final PostRepository postRepository;
  final AuthBloc authBloc;
  late StreamSubscription _authSubscription;
  
  PostBloc({
    required this.postRepository,
    required this.authBloc,
  }) : super(PostInitial()) {
    // 监听认证状态变化
    _authSubscription = authBloc.stream.listen((authState) {
      if (authState is Authenticated) {
        add(LoadPosts());
      }
    });
    
    on<LoadPosts>(_onLoadPosts);
    on<RefreshPosts>(_onRefreshPosts);
    on<CreatePost>(_onCreatePost);
    on<LikePost>(_onLikePost);
  }
  
  Future<void> _onLoadPosts(LoadPosts event, Emitter<PostState> emit) async {
    if (state is PostsLoaded && (state as PostsLoaded).hasReachedMax) {
      return;
    }
    
    emit(PostLoading());
    
    try {
      final currentState = state;
      final posts = await postRepository.getPosts(
        offset: currentState is PostsLoaded ? currentState.posts.length : 0,
        limit: 20,
      );
      
      if (posts.isEmpty) {
        emit((state as PostsLoaded).copyWith(hasReachedMax: true));
      } else {
        emit(
          currentState is PostsLoaded
              ? currentState.copyWith(
                  posts: currentState.posts + posts,
                  hasReachedMax