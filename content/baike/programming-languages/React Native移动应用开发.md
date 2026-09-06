---
title: "React Native移动应用开发"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# React Native移动应用开发

# React Native 移动应用开发完全指南

## 1. React Native 新架构深度解析

### 1.1 传统架构的局限性

在传统 React Native 架构中，JavaScript 和原生代码通过 Bridge 进行通信，这带来了几个关键问题：

- **异步通信延迟**：所有跨桥通信都是异步的，导致 UI 更新存在延迟
- **序列化/反序列化开销**：数据需要 JSON 序列化，性能损耗大
- **单线程阻塞**：JavaScript 在单线程中运行，容易阻塞 UI 渲染

### 1.2 新架构三大支柱

#### 1.2.1 JSI (JavaScript Interface)

JSI 是新架构的核心基础，它允许 JavaScript 直接调用 C++ 对象，无需经过 JSON 序列化。

```cpp
// JSI 的 C++ 实现示例
#include <jsi/jsi.h>

using namespace facebook::jsi;

// 在 C++ 端暴露原生方法
class SampleModule : public jsi::HostObject {
public:
  jsi::Value get(Runtime& runtime, const PropNameID& prop) override {
    auto name = prop.utf8(runtime);
    if (name == "multiply") {
      return Function::createFromHostFunction(
        runtime,
        PropNameID::forAscii(runtime, "multiply"),
        2, // 参数数量
        [](Runtime& runtime,
           const Value& thisValue,
           const Value* arguments,
           size_t count) -> Value {
          // 直接操作数值，无需序列化
          double a = arguments[0].getNumber();
          double b = arguments[1].getNumber();
          return Value(a * b);
        });
    }
    return Value::undefined();
  }
};

// JS 端的调用变得非常简单
const result = global.nativeModule.multiply(5, 3); // 直接返回 15
```

#### 1.2.2 Fabric 渲染器

Fabric 是新的渲染系统，重构了视图管理逻辑：

```javascript
// Fabric 组件示例
import React from 'react';
import { View, Text } from 'react-native';
import { requireNativeComponent } from 'react-native';

// 原生组件声明
const FabricComponent = requireNativeComponent('FabricView');

const MyFabricView = ({ backgroundColor, children }) => {
  return (
    <FabricComponent
      style={{ flex: 1, backgroundColor }}
      // 支持直接传递复杂数据结构
      config={{
        borderRadius: 10,
        shadow: {
          color: 'black',
          opacity: 0.5,
          radius: 10,
        }
      }}
    >
      {children}
    </FabricComponent>
  );
};
```

Fabric 的核心优势：
- **同步渲染**：支持同步的测量和布局
- **并发特性**：与 React 18 的并发特性深度集成
- **直接操作**：支持组件的直接操作，减少重渲染

#### 1.2.3 TurboModules

TurboModules 是新的原生模块系统，支持按需加载和类型安全：

```javascript
// TypeScript 类型定义
interface Spec extends TurboModule {
  getConstants(): {
    PI: number;
    E: number;
  };
  multiply(a: number, b: number): Promise<number>;
  divide(a: number, b: number): number; // 同步方法
}

// 在 JS 端使用
import { TurboModuleRegistry } from 'react-native';
const MathModule = TurboModuleRegistry.getEnforcing<Spec>('MathModule');

// 同步调用
const result = MathModule.divide(10, 2); // 直接返回 5

// 异步调用
const asyncResult = await MathModule.multiply(5, 3);
```

TurboModules 的优势：
- **懒加载**：只在首次使用时加载
- **类型安全**：完整的 TypeScript 支持
- **共享机制**：可跨多个 React Native 实例共享

### 1.3 新旧架构兼容策略

```javascript
// 渐进式迁移示例
import { FeatureFlag } from './featureFlags';

const useNewArchitecture = () => {
  // 通过特性标志控制
  return FeatureFlag.isEnabled('NEW_ARCHITECTURE');
};

const NativeComponent = useNewArchitecture() 
  ? require('./FabricComponent')
  : require('./LegacyComponent');

export default NativeComponent;
```

## 2. 核心组件与布局系统

### 2.1 Flexbox 深度应用

React Native 的 Flexbox 实现与 Web 有些关键差异：

```javascript
// 复杂的 Flexbox 布局示例
const DashboardLayout = () => {
  return (
    <View style={styles.container}>
      {/* 顶部导航栏 - 固定高度 */}
      <View style={styles.header}>
        <Text>标题</Text>
      </View>
      
      {/* 主内容区 - 可滚动 */}
      <ScrollView style={styles.mainContent}>
        <View style={styles.gridContainer}>
          {/* 使用 flexWrap 实现网格 */}
          {Array(12).fill(0).map((_, index) => (
            <View key={index} style={styles.gridItem}>
              <Text>Item {index + 1}</Text>
            </View>
          ))}
        </View>
        
        {/* 嵌套的 Flexbox 布局 */}
        <View style={styles.cardRow}>
          <View style={styles.card}>
            <Text>Card 1</Text>
          </View>
          <View style={styles.card}>
            <Text>Card 2</Text>
          </View>
          <View style={styles.card}>
            <Text>Card 3</Text>
          </View>
        </View>
      </ScrollView>
      
      {/* 底部标签栏 - 固定位置 */}
      <View style={styles.tabBar}>
        <TabButton icon="home" />
        <TabButton icon="search" />
        <TabButton icon="profile" />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    height: 60,
    paddingTop: Platform.OS === 'ios' ? 44 : 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  mainContent: {
    flex: 1,
    padding: 16,
  },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  gridItem: {
    width: '48%', // 两列布局
    height: 100,
    backgroundColor: 'white',
    marginBottom: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  card: {
    flex: 1,
    marginHorizontal: 4,
    height: 150,
    backgroundColor: 'white',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tabBar: {
    height: 50,
    backgroundColor: 'white',
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
});
```

### 2.2 SafeAreaView 的正确使用

SafeAreaView 在不同平台和设备上的处理策略：

```javascript
import { SafeAreaView, SafeAreaProvider } from 'react-native-safe-area-context';

const SafeScreen = ({ children }) => {
  return (
    <SafeAreaProvider>
      <SafeAreaView 
        style={{ flex: 1, backgroundColor: 'white' }}
        edges={['top', 'left', 'right']} // 自定义安全边
      >
        {children}
      </SafeAreaView>
    </SafeAreaProvider>
  );
};

// 带有动态安全区域的自定义Hook
const useSafeInsets = () => {
  const insets = useSafeAreaInsets();
  
  return {
    paddingTop: insets.top,
    paddingBottom: insets.bottom,
    paddingHorizontal: Math.max(insets.left, insets.right),
    // 为刘海屏和摄像头挖孔添加额外处理
    dynamicTop: Platform.select({
      ios: insets.top,
      android: StatusBar.currentHeight || 0,
    }),
  };
};
```

### 2.3 FlatList 的高级用法

```javascript
const AdvancedFlatList = () => {
  const [data, setData] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const flatListRef = useRef(null);

  // 初始加载
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async (page = 1) => {
    try {
      const response = await fetch(`https://api.example.com/items?page=${page}`);
      const newItems = await response.json();
      
      if (page === 1) {
        setData(newItems);
      } else {
        setData(prev => [...prev, ...newItems]);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  // 下拉刷新
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData(1);
    setRefreshing(false);
  };

  // 上拉加载更多
  const handleLoadMore = async () => {
    if (loadingMore) return;
    
    setLoadingMore(true);
    await loadData(Math.ceil(data.length / 20) + 1);
    setLoadingMore(false);
  };

  // 优化渲染项
  const renderItem = useCallback(({ item, index }) => (
    <ListItem
      item={item}
      onPress={() => handleItemPress(item)}
      // 使用 shouldItemUpdate 进行更精细的优化
      shouldUpdate={(prev, next) => prev.item.id !== next.item.id}
    />
  ), []);

  // 分组列表头
  const renderSectionHeader = useCallback(({ section }) => (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>{section.title}</Text>
    </View>
  ), []);

  // 关键配置项
  const keyExtractor = useCallback((item) => item.id.toString(), []);

  return (
    <SectionList
      ref={flatListRef}
      sections={data}
      renderItem={renderItem}
      renderSectionHeader={renderSectionHeader}
      keyExtractor={keyExtractor}
      onRefresh={handleRefresh}
      refreshing={refreshing}
      onEndReached={handleLoadMore}
      onEndReachedThreshold={0.5} // 当剩余50%时触发加载
      removeClippedSubviews={true} // 移除屏幕外的视图
      maxToRenderPerBatch={10} // 每批渲染数量
      updateCellsBatchingPeriod={50} // 更新批处理周期
      windowSize={10} // 窗口大小（屏幕数）
      initialNumToRender={10}
      // 支持滚动到指定索引
      onViewableItemsChanged={useCallback(({ viewableItems }) => {
        console.log('Viewable items:', viewableItems);
      }, [])}
      // 自定义空状态
      ListEmptyComponent={<EmptyState />}
      // 自定义加载指示器
      ListFooterComponent={loadingMore ? <ActivityIndicator /> : null}
      // 性能优化
      getItemLayout={(data, index) => ({
        length: ITEM_HEIGHT,
        offset: ITEM_HEIGHT * index,
        index,
      })}
    />
  );
};
```

## 3. 导航系统 (React Navigation v6+)

### 3.1 多层嵌套导航结构

```javascript
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { createMaterialTopTabNavigator } from '@react-navigation/material-top-tabs';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();
const Drawer = createDrawerNavigator();
const TopTab = createMaterialTopTabNavigator();

// 顶部标签页（如：分类、推荐、关注）
const CategoryTabs = () => (
  <TopTab.Navigator
    tabBarOptions={{
      scrollEnabled: true,
      tabStyle: { width: 100 },
      indicatorStyle: { backgroundColor: '#007AFF' },
    }}
  >
    <TopTab.Screen name="推荐" component={RecommendScreen} />
    <TopTab.Screen name="科技" component={TechScreen} />
    <TopTab.Screen name="娱乐" component={EntertainmentScreen} />
    <TopTab.Screen name="体育" component={SportsScreen} />
  </TopTab.Navigator>
);

// 底部标签导航
const MainTabs = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName;
        if (route.name === '首页') {
          iconName = focused ? 'home' : 'home-outline';
        } else if (route.name === '发现') {
          iconName = focused ? 'compass' : 'compass-outline';
        }
        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: '#007AFF',
      tabBarInactiveTintColor: 'gray',
      tabBarBadgeStyle: { backgroundColor: 'red' },
    })}
  >
    <Tab.Screen 
      name="首页" 
      component={HomeStack}
      options={{ 
        tabBarBadge: 3, // 未读消息数
        headerShown: false 
      }}
    />
    <Tab.Screen name="发现" component={DiscoverScreen} />
    <Tab.Screen name="消息" component={MessageScreen} />
    <Tab.Screen name="我的" component={ProfileScreen} />
  </Tab.Navigator>
);

// 抽屉导航包裹主界面
const MainDrawer = () => (
  <Drawer.Navigator
    drawerContent={(props) => <CustomDrawerContent {...props} />}
    screenOptions={{
      drawerType: 'front', // 'back', 'front', 'slide'
      drawerStyle: {
        width: 280,
      },
    }}
  >
    <Drawer.Screen 
      name="主界面" 
      component={MainTabs}
      options={{ headerShown: false }}
    />
    <Drawer.Screen name="设置" component={SettingsScreen} />
    <Drawer.Screen name="关于" component={AboutScreen} />
  </Drawer.Navigator>
);

// 根导航栈
const AppNavigator = () => {
  const { isAuthenticated } = useAuth();
  
  return (
    <NavigationContainer
      linking={deepLinkingConfig}
      fallback={<SplashScreen />}
      onStateChange={(state) => {
        // 路由变化分析
        analytics.logScreenView(getCurrentRouteName(state));
      }}
    >
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          animation: 'slide_from_right',
        }}
      >
        {isAuthenticated ? (
          <>
            <Stack.Screen name="Main" component={MainDrawer} />
            <Stack.Screen 
              name="ProductDetail" 
              component={ProductDetailScreen}
              options={{
                headerShown: true,
                title: '商品详情',
                headerBackTitleVisible: false,
              }}
            />
            <Stack.Screen 
              name="Cart" 
              component={CartScreen}
              options={{
                presentation: 'modal', // 模态呈现
                animation: 'slide_from_bottom',
              }}
            />
          </>
        ) : (
          <>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Register" component={RegisterScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};
```

### 3.2 深度链接配置

```javascript
const deepLinkingConfig = {
  prefixes: ['myapp://', 'https://myapp.com'],
  config: {
    screens: {
      Main: {
        screens: {
          首页: 'home',
          发现: 'discover',
          产品详情: {
            path: 'product/:id',
            parse: {
              id: (id) => `product-${id}`,
            },
          },
        },
      },
      Login: 'login',
      注册: 'register',
    },
  },
};
```

## 4. 现代状态管理方案

### 4.1 Zustand 状态管理

```javascript
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { immer } from 'zustand/middleware/immer';

// 购物车状态管理
const useCartStore = create(
  persist(
    immer((set, get) => ({
      // 状态
      items: [],
      totalAmount: 0,
      totalItems: 0,
      
      // 操作
      addItem: (product, quantity = 1) => {
        set((state) => {
          const existingItem = state.items.find(item => item.id === product.id);
          
          if (existingItem) {
            existingItem.quantity += quantity;
          } else {
            state.items.push({
              ...product,
              quantity,
              addedAt: new Date().toISOString(),
            });
          }
          
          // 重新计算总数
          state.totalItems = state.items.reduce(
            (sum, item) => sum + item.quantity, 0
          );
          state.totalAmount = state.items.reduce(
            (sum, item) => sum + (item.price * item.quantity), 0
          );
        });
      },
      
      removeItem: (productId) => {
        set((state) => {
          state.items = state.items.filter(item => item.id !== productId);
          // 重新计算
          state.totalItems = state.items.reduce(
            (sum, item) => sum + item.quantity, 0
          );
          state.totalAmount = state.items.reduce(
            (sum, item) => sum + (item.price * item.quantity), 0
          );
        });
      },
      
      updateQuantity: (productId, quantity) => {
        set((state) => {
          const item = state.items.find(item => item.id === productId);
          if (item) {
            item.quantity = quantity;
            // 重新计算
            state.totalItems = state.items.reduce(
              (sum, item) => sum + item.quantity, 0
            );
            state.totalAmount = state.items.reduce(
              (sum, item) => sum + (item.price * item.quantity), 0
            );
          }
        });
      },
      
      clearCart: () => {
        set({ items: [], totalAmount: 0, totalItems: 0 });
      },
      
      // 异步操作
      syncCartWithServer: async () => {
        try {
          const { items } = get();
          await api.syncCart(items);
          set({ lastSync: new Date().toISOString() });
        } catch (error) {
          console.error('Cart sync failed:', error);
        }
      },
    })),
    {
      name: 'cart-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        items: state.items,
        totalAmount: state.totalAmount,
        totalItems: state.totalItems,
      }),
    }
  )
);

// 用户认证状态
const useAuthStore = create((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  
  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const response = await api.login({ email, password });
      const { user, token } = response.data;
      
      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      });
      
      // 存储token
      await AsyncStorage.setItem('authToken', token);
      
      return { success: true };
    } catch (error) {
      set({ isLoading: false });
      return { success: false, error: error.message };
    }
  },
  
  logout: async () => {
    await AsyncStorage.removeItem('authToken');
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },
  
  initialize: async () => {
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      try {
        const user = await api.verifyToken(token);
        set({
          user,
          token,
          isAuthenticated: true,
        });
      } catch (error) {
        await AsyncStorage.removeItem('authToken');
      }
    }
  },
}));

// 在组件中使用
const ProductCard = ({ product }) => {
  const addToCart = useCartStore(state => state.addItem);
  const cartItems = useCartStore(state => state.items);
  const isInCart = cartItems.some(item => item.id === product.id);
  
  return (
    <View style={styles.productCard}>
      <Text>{product.name}</Text>
      <Text>¥{product.price}</Text>
      <Button
        title={isInCart ? '已加入购物车' : '加入购物车'}
        onPress={() => addToCart(product)}
        disabled={isInCart}
      />
    </View>
  );
};
```

### 4.2 Jotai 原子状态管理

```javascript
import { atom, useAtom, useAtomValue, useSetAtom } from 'jotai';
import { atomWithStorage, atomWithObservable } from 'jotai/utils';
import { focusAtom } from 'jotai-optics';

// 基础原子
const countAtom = atom(0);
const doubledCountAtom = atom((get) => get(countAtom) * 2);

// 持久化原子
const themeAtom = atomWithStorage('theme', 'light');

// 用户信息原子
const userAtom = atomWithStorage('user', null);

// 从用户原子派生的焦点原子
const userNameAtom = focusAtom(userAtom, (optic) => optic.prop('name'));
const userEmailAtom = focusAtom(userAtom, (optic) => optic.prop('email'));

// 可写派生原子
const incrementAtom = atom(
  (get) => get(countAtom),
  (get, set, amount = 1) => {
    set(countAtom, get(countAtom) + amount);
  }
);

// 异步原子
const fetchUserAtom = atom(
  async (get) => {
    const userId = get(userIdAtom);
    if (!userId) return null;
    
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
  }
);

// 可观察原子（用于实时数据）
const locationAtom = atomWithObservable(() => 
  new Observable(subscriber => {
    const watchId = Geolocation.watchPosition(
      (position) => subscriber.next(position),
      (error) => subscriber.error(error)
    );
    
    return () => Geolocation.clearWatch(watchId);
  })
);

// 购物车原子（类似Zustand实现）
const cartItemsAtom = atom([]);
const cartTotalAtom = atom(
  (get) => {
    const items = get(cartItemsAtom);
    return items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  }
);

const addToCartAtom = atom(
  null,
  (get, set, product) => {
    const items = get(cartItemsAtom);
    const existing = items.find(item => item.id === product.id);
    
    if (existing) {
      set(cartItemsAtom, items.map(item =>
        item.id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      set(cartItemsAtom, [...items, { ...product, quantity: 1 }]);
    }
  }
);

// 在组件中使用
const Counter = () => {
  const [count, setCount] = useAtom(countAtom);
  const doubled = useAtomValue(doubledCountAtom);
  const increment = useSetAtom(incrementAtom);
  
  return (
    <View>
      <Text>Count: {count}</Text>
      <Text>Doubled: {doubled}</Text>
      <Button title="Increment" onPress={() => increment(1)} />
      <Button title="Double" onPress={() => increment(2)} />
    </View>
  );
};

const UserForm = () => {
  const [name, setName] = useAtom(userNameAtom);
  const [email, setEmail] = useAtom(userEmailAtom);
  const user = useAtomValue(userAtom);
  
  return (
    <View>
      <TextInput
        value={name}
        onChangeText={setName}
        placeholder="Name"
      />
      <TextInput
        value={email}
        onChangeText={setEmail}
        placeholder="Email"
        keyboardType="email-address"
      />
      {user && (
        <Text>Welcome, {user.name}!</Text>
      )}
    </View>
  );
};
```

## 5. 网络请求与数据缓存

### 5.1 完整的网络层封装

```javascript
// services/api.js
import axios from 'axios';
import { Platform } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import EncryptedStorage from 'react-native-encrypted-storage';

const API_BASE_URL = __DEV__ 
  ? 'https://dev-api.myapp.com'
  : 'https://api.myapp.com';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Platform': Platform.OS,
    'X-App-Version': '1.0.0',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  async (config) => {
    // 添加认证token
    try {
      const token = await EncryptedStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Failed to get auth token:', error);
    }
    
    // 添加请求ID用于追踪
    config.headers['X-Request-ID'] = generateUUID();
    
    // 检查网络连接
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) {
      throw new Error('No network connection');
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 记录响应时间
    const duration = Date.now() - response.config.meta?.requestTime;
    console.log(`API Call: ${response.config.url} - ${duration}ms`);
    
    // 处理业务逻辑错误
    if (response.data.code && response.data.code !== 200) {
      throw new APIError(response.data.message, response.data.code);
    }
    
    return response.data;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // 处理token过期
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = await EncryptedStorage.getItem('refresh_token');
        const response = await apiClient.post('/auth/refresh', {
          refreshToken,
        });
        
        const { accessToken } = response.data;
        await EncryptedStorage.setItem('auth_token', accessToken);
        
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // 跳转到登录页面
        navigationRef.navigate('Login');
        throw refreshError;
      }
    }
    
    // 网络错误重试
    if (error.code === 'ECONNABORTED' || error.message === 'Network Error') {
      if (originalRequest.retryCount < 3) {
        originalRequest.retryCount = (originalRequest.retryCount || 0) + 1;
        const delay = Math.pow(2, originalRequest.retryCount) * 1000;
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return apiClient(originalRequest);
      }
    }
    
    throw error;
  }
);

// API服务类
class APIService {
  // 获取商品列表
  static async getProducts(params = {}) {
    return apiClient.get('/products', { params });
  }
  
  // 搜索商品
  static async searchProducts(query, filters = {}) {
    return apiClient.get('/products/search', {
      params: { q: query, ...filters }
    });
  }
  
  // 上传图片
  static async uploadImage(uri, onProgress) {
    const formData = new FormData();
    const filename = uri.split('/').pop();
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `image/${match[1]}` : 'image';
    
    formData.append('image', {
      uri: Platform.OS === 'ios' ? uri.replace('file://', '') : uri,
      name: filename,
      type,
    });
    
    return apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const progress = progressEvent.loaded / progressEvent.total;
        onProgress?.(progress);
      },
    });
  }
  
  // 批量请求
  static async batchRequest(requests) {
    const promises = requests.map(request => {
      const { method, url, data, params } = request;
      return apiClient[method.toLowerCase()](url, { data, params })
        .then(response => ({ success: true, data: response }))
        .catch(error => ({ success: false, error }));
    });
    
    return Promise.all(promises);
  }
}

export { apiClient, APIService };
```

### 5.2 数据缓存策略

```javascript
// utils/cacheManager.js
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MMKV } from 'react-native-mmkv';
import { Observable, Subscriber } from 'rxjs';

// 使用 MMKV 进行快速存储
const storage = new MMKV();

class CacheManager {
  static CACHE_PREFIX = '@Cache:';
  static DEFAULT_TTL = 24 * 60 * 60 * 1000; // 24小时
  
  // 设置缓存
  static async set(key, data, ttl = this.DEFAULT_TTL) {
    const cacheKey = `${this.CACHE_PREFIX}${key}`;
    const cacheItem = {
      data,
      timestamp: Date.now(),
      ttl,
      version: '1.0',
    };
    
    try {
      // 同步写入MMKV（快速）
      storage.set(cacheKey, JSON.stringify(cacheItem));
      return true;
    } catch (error) {
      // 回退到AsyncStorage
      await AsyncStorage.setItem(cacheKey, JSON.stringify(cacheItem));
      return true;
    }
  }
  
  // 获取缓存
  static async get(key) {
    const cacheKey = `${this.CACHE_PREFIX}${key}`;
    
    try {
      let cacheData;
      
      // 先尝试从MMKV读取
      cacheData = storage.getString(cacheKey);
      
      if (!cacheData) {
        // 回退到AsyncStorage
        cacheData = await AsyncStorage.getItem(cacheKey);
      }
      
      if (!cacheData) return null;
      
      const cacheItem = JSON.parse(cacheData);
      const isExpired = Date.now() - cacheItem.timestamp > cacheItem.ttl;
      
      if (isExpired) {
        this.remove(key);
        return null;
      }
      
      return cacheItem.data;
    } catch (error) {
      console.error('Cache read error:', error);
      return null;
    }
  }
  
  // 带回退的缓存获取
  static async getWithFallback(key, fetchFunction, options = {}) {
    const { forceRefresh = false, ttl = this.DEFAULT_TTL } = options;
    
    // 尝试获取缓存
    if (!forceRefresh) {
      const cachedData = await this.get(key);
      if (cachedData) {
        // 后台更新缓存
        if (options.backgroundRefresh) {
          this.refreshInBackground(key, fetchFunction, ttl);
        }
        return cachedData;
      }
    }
    
    // 缓存未命中，获取新数据
    try {
      const freshData = await fetchFunction();
      await this.set(key, freshData, ttl);
      return freshData;
    } catch (error) {
      // 如果请求失败，尝试返回过期的缓存
      if (options.allowStale) {
        return this.get(key);
      }
      throw error;
    }
  }
  
  // 后台刷新缓存
  static async refreshInBackground(key, fetchFunction, ttl) {
    try {
      const freshData = await fetchFunction();
      await this.set(key, freshData, ttl);
    } catch (error) {
      console.error('Background cache refresh failed:', error);
    }
  }
  
  // 清理过期缓存
  static async cleanup() {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith(this.CACHE_PREFIX));
      
      const expiredKeys = [];
      
      for (const key of cacheKeys) {
        const cacheData = await AsyncStorage.getItem(key);
        if (cacheData) {
          const cacheItem = JSON.parse(cacheData);
          if (Date.now() - cacheItem.timestamp > cacheItem.ttl) {
            expiredKeys.push(key);
          }
        }
      }
      
      if (expiredKeys.length > 0) {
        await AsyncStorage.multiRemove(expiredKeys);
      }
    } catch (error) {
      console.error('Cache cleanup failed:', error);
    }
  }
  
  // 清空所有缓存
  static async clearAll() {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith(this.CACHE_PREFIX));
      
      if (cacheKeys.length > 0) {
        await AsyncStorage.multiRemove(cacheKeys);
      }
      
      // 清理MMKV存储
      storage.clearAll();
    } catch (error) {
      console.error('Cache clear failed:', error);
    }
  }
}

// 使用示例
const useCachedProducts = (categoryId) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadProducts = async () => {
      try {
        setLoading(true);
        
        const data = await CacheManager.getWithFallback(
          `products_${categoryId}`,
          () => APIService.getProducts({ category: categoryId }),
          {
            ttl: 60 * 60 * 1000, // 1小时缓存
            allowStale: true, // 允许返回过期数据
            backgroundRefresh: true,
          }
        );
        
        setProducts(data.products);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    loadProducts();
  }, [categoryId]);
  
  return { products, loading, error };
};

export { CacheManager };
```

## 6. 原生模块桥接

### 6.1 iOS 原生模块

```objectc
// CalendarModule.h
#import <React/RCTBridgeModule.h>
#import <React/RCTEventEmitter.h>

@interface CalendarModule : RCTEventEmitter <RCTBridgeModule>
@end

// CalendarModule.m
#import "CalendarModule.h"
#import <EventKit/EventKit.h>

@implementation CalendarModule

RCT_EXPORT_MODULE();

// 同步方法
RCT_EXPORT_SYNCHRONOUS_TYPED_METHOD(NSString *, getCalendarAccessStatus) {
  EKAuthorizationStatus status = [EKEventStore authorizationStatusForEntityType:EKEntityTypeEvent];
  
  switch (status) {
    case EKAuthorizationStatusAuthorized:
      return @"authorized";
    case EKAuthorizationStatusDenied:
      return @"denied";
    case EKAuthorizationStatusRestricted: