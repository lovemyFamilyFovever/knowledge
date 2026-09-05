---
title: "Python高级编程完全指南"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Python高级编程完全指南

# Python高级编程完全指南

## 1. 装饰器的高级用法

### 1.1 带参数的装饰器（装饰器工厂）

装饰器工厂是一个返回装饰器的函数，这允许我们创建更灵活的装饰器。

```python
import functools
import time
import logging
from typing import Any, Callable, TypeVar, cast

# 类型变量用于保持函数签名
F = TypeVar('F', bound=Callable[..., Any])

def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    带参数的重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要捕获的异常类型
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logging.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        return cast(F, wrapper)
    return decorator

# 使用示例
@retry(max_attempts=5, delay=0.5, exceptions=(ConnectionError, TimeoutError))
def fetch_data(url: str) -> str:
    """模拟网络请求"""
    if "fail" in url:
        raise ConnectionError("Connection failed")
    return f"Data from {url}"

# 实际应用场景：API调用重试机制
@retry(max_attempts=3, delay=2.0, exceptions=(Exception,))
def call_external_api(endpoint: str, data: dict) -> dict:
    """调用外部API的包装函数"""
    import requests
    response = requests.post(endpoint, json=data, timeout=10)
    response.raise_for_status()
    return response.json()

# 多参数装饰器的更复杂示例
def validate_params(**validators):
    """
    参数验证装饰器工厂
    
    使用示例:
        @validate_params(
            age=lambda x: 0 < x < 150,
            name=lambda x: len(x) > 0
        )
        def create_user(name: str, age: int):
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数签名和参数绑定
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # 验证参数
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"Validation failed for parameter '{param_name}': {value}"
                        )
            return func(*args, **kwargs)
        return cast(F, wrapper)
    return decorator

# 使用参数验证装饰器
@validate_params(
    age=lambda x: 0 < x < 150,
    name=lambda x: isinstance(x, str) and len(x.strip()) > 0,
    email=lambda x: '@' in x
)
def create_user(name: str, age: int, email: str):
    """创建用户"""
    return {"name": name, "age": age, "email": email}

# 测试
try:
    result = create_user("Alice", 25, "alice@example.com")
    print(f"User created: {result}")
    
    # 这将引发验证错误
    # create_user("", -5, "invalid-email")
except ValueError as e:
    print(f"Validation error: {e}")
```

### 1.2 类装饰器

类装饰器可以用于修改或增强类的行为，实现元编程模式。

```python
from typing import Type, Any, Dict, List
import json
from dataclasses import dataclass, fields, asdict

def auto_repr(cls):
    """自动实现__repr__的类装饰器"""
    def __repr__(self):
        class_name = self.__class__.__name__
        attributes = ', '.join(
            f"{field.name}={getattr(self, field.name)!r}"
            for field in fields(self)
        )
        return f"{class_name}({attributes})"
    
    cls.__repr__ = __repr__
    return cls

def register(registry: Dict[str, Type]):
    """将类注册到全局注册表的装饰器"""
    def decorator(cls):
        registry[cls.__name__] = cls
        return cls
    return decorator

# 全局注册表
SERIALIZABLE_CLASSES = {}

def serializable(cls):
    """
    使类可序列化的装饰器
    添加to_json和from_json方法
    """
    def to_json(self):
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(**data)
    
    cls.to_json = to_json
    cls.from_json = from_json
    register(SERIALIZABLE_CLASSES)(cls)
    
    return cls

# 使用示例
@auto_repr
@serializable
@dataclass
class User:
    name: str
    age: int
    email: str
    preferences: Dict[str, Any] = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}

# 高级类装饰器：实现观察者模式
def observable(cls):
    """使类可观察的装饰器"""
    class ObservableWrapper(cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._observers: List[Callable] = []
            self._events: Dict[str, List[Callable]] = {}
        
        def add_observer(self, event: str, callback: Callable):
            """添加事件观察者"""
            if event not in self._events:
                self._events[event] = []
            self._events[event].append(callback)
        
        def _notify(self, event: str, **kwargs):
            """通知所有观察者"""
            if event in self._events:
                for callback in self._events[event]:
                    callback(self, event, **kwargs)
        
        def __setattr__(self, name, value):
            old_value = getattr(self, name, None) if hasattr(self, name) else None
            super().__setattr__(name, value)
            if old_value != value:
                self._notify('attribute_changed', 
                           attribute=name, 
                           old_value=old_value, 
                           new_value=value)
    
    ObservableWrapper.__name__ = cls.__name__
    ObservableWrapper.__qualname__ = cls.__qualname__
    
    return ObservableWrapper

# 应用观察者装饰器
@observable
@dataclass
class ObservableConfig:
    debug: bool = False
    log_level: str = "INFO"
    max_connections: int = 100

# 使用示例
config = ObservableConfig()

def on_config_change(sender, event, **kwargs):
    print(f"Config changed: {kwargs['attribute']} from {kwargs['old_value']} to {kwargs['new_value']}")

config.add_observer('attribute_changed', on_config_change)

# 修改属性会触发通知
config.debug = True  # 输出: Config changed: debug from False to True
config.log_level = "DEBUG"  # 输出: Config changed: log_level from INFO to DEBUG

# 类装饰器工厂：允许带参数
def add_methods(**methods):
    """
    为类添加方法的装饰器工厂
    
    使用示例:
        @add_methods(
            greet=lambda self: f"Hello, I'm {self.name}",
            is_adult=lambda self: self.age >= 18
        )
        class Person:
            def __init__(self, name, age):
                self.name = name
                self.age = age
    """
    def decorator(cls):
        for method_name, method_func in methods.items():
            setattr(cls, method_name, method_func)
        return cls
    return decorator

# 使用带参数的类装饰器
@add_methods(
    greet=lambda self: f"Hello, I'm {self.name}",
    is_adult=lambda self: self.age >= 18,
    to_dict=lambda self: {"name": self.name, "age": self.age}
)
class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

person = Person("Alice", 25)
print(person.greet())  # 输出: Hello, I'm Alice
print(person.is_adult())  # 输出: True
print(person.to_dict())  # 输出: {'name': 'Alice', 'age': 25}
```

## 2. 元类编程

### 2.1 type()作为元类

```python
from typing import Dict, Type, Any

# 使用type()动态创建类
def create_validator_class(field_name: str, validation_func: callable) -> Type:
    """动态创建字段验证器类"""
    
    def __init__(self, value):
        self.value = value
        self.validate()
    
    def validate(self):
        if not validation_func(self.value):
            raise ValueError(f"Invalid {field_name}: {self.value}")
    
    def __repr__(self):
        return f"{field_name.title()}Validator({self.value!r})"
    
    # 使用type创建类
    class_dict = {
        '__init__': __init__,
        'validate': validate,
        '__repr__': __repr__,
        'field_name': field_name,
    }
    
    return type(
        f"{field_name.title()}Validator",
        (object,),
        class_dict
    )

# 创建不同的验证器类
EmailValidator = create_validator_class(
    "email",
    lambda x: isinstance(x, str) and '@' in x and '.' in x.split('@')[1]
)

AgeValidator = create_validator_class(
    "age",
    lambda x: isinstance(x, int) and 0 < x < 150
)

# 使用动态创建的类
try:
    email_validator = EmailValidator("alice@example.com")
    print(f"Valid: {email_validator}")
    
    age_validator = AgeValidator(25)
    print(f"Valid: {age_validator}")
    
    # 这将引发验证错误
    # invalid_email = EmailValidator("invalid-email")
except ValueError as e:
    print(f"Error: {e}")
```

### 2.2 自定义元类

```python
from typing import Any, Dict, Tuple, Type
import inspect

class SingletonMeta(type):
    """
    单例元类
    确保使用此元类的类只有一个实例
    """
    _instances: Dict[Type, Any] = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
    
    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        # 防止通过继承创建多个实例
        if cls not in cls._instances:
            cls._instances[cls] = None

class DatabaseConnection(metaclass=SingletonMeta):
    """使用单例元类的数据库连接类"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.connection = None
        print(f"Creating connection to {host}:{port}")
    
    def connect(self):
        if self.connection is None:
            self.connection = f"Connection to {self.host}:{self.port}"
            print("Connected to database")
        return self.connection

# 验证单例行为
db1 = DatabaseConnection("localhost", 5432)
db2 = DatabaseConnection("localhost", 3306)  # 参数会被忽略
print(db1 is db2)  # True
print(db1.port)  # 5432，而不是3306

class ValidationMeta(type):
    """
    验证元类
    自动为类添加验证方法
    """
    
    def __new__(mcs, name, bases, namespace):
        # 获取类注解
        annotations = namespace.get('__annotations__', {})
        
        # 为每个带注解的字段创建验证方法
        for field_name, field_type in annotations.items():
            if field_name.startswith('_'):
                continue  # 跳过私有字段
                
            # 创建getter和setter
            def make_property(field_name, field_type):
                def getter(self):
                    return getattr(self, f'_{field_name}', None)
                
                def setter(self, value):
                    if not isinstance(value, field_type):
                        raise TypeError(
                            f"{field_name} must be of type {field_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
                    setattr(self, f'_{field_name}', value)
                
                return property(getter, setter)
            
            namespace[field_name] = make_property(field_name, field_type)
        
        return super().__new__(mcs, name, bases, namespace)

class ValidatedModel(metaclass=ValidationMeta):
    """使用验证元类的基础模型"""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        fields = ', '.join(
            f"{key}={getattr(self, key)!r}"
            for key in self.__annotations__
            if not key.startswith('_')
        )
        return f"{self.__class__.__name__}({fields})"

# 使用验证元类
class User(ValidatedModel):
    name: str
    age: int
    email: str

# 测试验证
try:
    user = User(name="Alice", age=25, email="alice@example.com")
    print(user)  # User(name='Alice', age=25, email='alice@example.com')
    
    # 类型验证
    user.age = "twenty-five"  # 抛出TypeError
except TypeError as e:
    print(f"Type error: {e}")

class AutoInitMeta(type):
    """
    自动生成__init__方法的元类
    基于类注解自动初始化属性
    """
    
    def __new__(mcs, name, bases, namespace):
        annotations = namespace.get('__annotations__', {})
        
        if '__init__' not in namespace and annotations:
            def __init__(self, **kwargs):
                for field_name, field_type in annotations.items():
                    if field_name in kwargs:
                        setattr(self, field_name, kwargs[field_name])
                    else:
                        # 设置默认值
                        if field_type == str:
                            setattr(self, field_name, "")
                        elif field_type == int:
                            setattr(self, field_name, 0)
                        elif field_type == float:
                            setattr(self, field_name, 0.0)
                        elif field_type == bool:
                            setattr(self, field_name, False)
                        elif field_type == list:
                            setattr(self, field_name, [])
                        elif field_type == dict:
                            setattr(self, field_name, {})
                        else:
                            setattr(self, field_name, None)
            
            namespace['__init__'] = __init__
        
        return super().__new__(mcs, name, bases, namespace)

class AutoModel(metaclass=AutoInitMeta):
    """使用自动初始化元类的基类"""
    
    def to_dict(self):
        return {key: getattr(self, key) for key in self.__annotations__}

class Product(AutoModel):
    name: str
    price: float
    quantity: int
    in_stock: bool

# 测试自动初始化
product = Product(name="Widget", price=9.99, quantity=100)
print(product.to_dict())
# {'name': 'Widget', 'price': 9.99, 'quantity': 100, 'in_stock': False}
```

### 2.3 __init_subclass__ (Python 3.6+)

```python
from typing import Dict, List, Type
import json

class PluginRegistry:
    """插件注册表基类"""
    _plugins: Dict[str, Type['PluginRegistry']] = {}
    
    def __init_subclass__(cls, plugin_name: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        
        name = plugin_name or cls.__name__.lower()
        if name in PluginRegistry._plugins:
            raise ValueError(f"Plugin '{name}' already registered")
        
        PluginRegistry._plugins[name] = cls
        print(f"Registered plugin: {name}")
    
    @classmethod
    def get_plugin(cls, name: str) -> Type['PluginRegistry']:
        if name not in cls._plugins:
            raise KeyError(f"Plugin '{name}' not found")
        return cls._plugins[name]
    
    @classmethod
    def list_plugins(cls) -> List[str]:
        return list(cls._plugins.keys())

# 使用__init_subclass__自动注册插件
class JSONParser(PluginRegistry, plugin_name="json"):
    """JSON解析器插件"""
    
    @staticmethod
    def parse(data: str) -> dict:
        return json.loads(data)
    
    @staticmethod
    def serialize(data: dict) -> str:
        return json.dumps(data)

class XMLParser(PluginRegistry, plugin_name="xml"):
    """XML解析器插件"""
    
    @staticmethod
    def parse(data: str) -> dict:
        # 简化的XML解析示例
        import xml.etree.ElementTree as ET
        root = ET.fromstring(data)
        return {child.tag: child.text for child in root}
    
    @staticmethod
    def serialize(data: dict) -> str:
        root = ET.Element("data")
        for key, value in data.items():
            child = ET.SubElement(root, key)
            child.text = str(value)
        return ET.tostring(root, encoding='unicode')

# 查看已注册的插件
print("Available plugins:", PluginRegistry.list_plugins())
# 输出: Available plugins: ['json', 'xml']

# 使用插件
json_plugin = PluginRegistry.get_plugin("json")
data = json_plugin.parse('{"name": "test", "value": 123}')
print(data)  # {'name': 'test', 'value': 123}

# 更复杂的例子：ORM风格的模型注册
class ModelRegistry:
    """模型注册表，类似Django的模型系统"""
    _models: Dict[str, Type['BaseModel']] = {}
    
    def __init_subclass__(cls, table_name: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # 自动设置表名
        if not hasattr(cls, 'table_name'):
            cls.table_name = table_name or cls.__name__.lower() + 's'
        
        # 注册模型
        ModelRegistry._models[cls.__name__] = cls
        
        # 自动生成基础的CRUD方法
        if not hasattr(cls, 'objects'):
            cls.objects = cls._create_manager()
    
    @classmethod
    def _create_manager(cls):
        """创建模型管理器"""
        class Manager:
            def __init__(self, model):
                self.model = model
            
            def all(self):
                print(f"SELECT * FROM {self.model.table_name}")
                return []  # 实际实现会查询数据库
            
            def create(self, **kwargs):
                instance = self.model(**kwargs)
                print(f"INSERT INTO {self.model.table_name} ...")
                return instance
            
            def get(self, **kwargs):
                print(f"SELECT * FROM {self.model.table_name} WHERE ...")
                return self.model(**kwargs)
        
        return Manager(cls)

class BaseModel(ModelRegistry):
    """基础模型类"""
    
    def save(self):
        print(f"Saving {self.__class__.__name__}")
        # 实际实现会保存到数据库
    
    def delete(self):
        print(f"Deleting {self.__class__.__name__}")
        # 实际实现会从数据库删除

# 定义模型（会自动注册）
class User(BaseModel, table_name="users"):
    name: str
    email: str
    
    def full_info(self):
        return f"{self.name} ({self.email})"

class Post(BaseModel, table_name="posts"):
    title: str
    content: str
    author_id: int

# 使用注册的模型
print("Registered models:", list(ModelRegistry._models.keys()))
# 输出: Registered models: ['BaseModel', 'User', 'Post']

# 使用自动生成的管理器
User.objects.all()  # 输出: SELECT * FROM users
user = User.objects.create(name="Alice", email="alice@example.com")
print(user.full_info())  # Alice (alice@example.com)

Post.objects.all()  # 输出: SELECT * FROM posts
```

## 3. 描述符协议

### 3.1 数据描述符 vs 非数据描述符

```python
from typing import Any, Type

class NonDataDescriptor:
    """非数据描述符（只实现了__get__）"""
    
    def __init__(self, name: str):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        print(f"NonDataDescriptor.__get__ called for {self.name}")
        return f"Non-data value for {self.name}"

class DataDescriptor:
    """数据描述符（实现了__get__和__set__）"""
    
    def __init__(self, name: str, default: Any = None):
        self.name = name
        self.default = default
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        print(f"DataDescriptor.__get__ called for {self.name}")
        return getattr(obj, f'_{self.name}', self.default)
    
    def __set__(self, obj, value):
        print(f"DataDescriptor.__set__ called for {self.name}")
        setattr(obj, f'_{self.name}', value)
    
    def __delete__(self, obj):
        print(f"DataDescriptor.__delete__ called for {self.name}")
        if hasattr(obj, f'_{self.name}'):
            delattr(obj, f'_{self.name}')

class TypeEnforcingDescriptor:
    """类型强制描述符"""
    
    def __init__(self, name: str, expected_type: Type):
        self.name = name
        self.expected_type = expected_type
    
    def __set_name__(self, owner, name):
        """Python 3.6+自动调用，设置描述符名称"""
        self.name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, f'_{self.name}', None)
    
    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.name} must be of type {self.expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
        setattr(obj, f'_{self.name}', value)
    
    def __delete__(self, obj):
        if hasattr(obj, f'_{self.name}'):
            delattr(obj, f'_{self.name}')

# 使用描述符
class Person:
    # 数据描述符（优先级高于实例字典）
    name = TypeEnforcingDescriptor('name', str)
    age = TypeEnforcingDescriptor('age', int)
    
    # 非数据描述符（优先级低于实例字典）
    greeting = NonDataDescriptor('greeting')
    
    def __init__(self, name: str, age: int):
        self.name = name  # 触发TypeEnforcingDescriptor.__set__
        self.age = age    # 触发TypeEnforcingDescriptor.__set__
    
    def __str__(self):
        return f"Person(name={self.name}, age={self.age})"

# 测试描述符行为
person = Person("Alice", 25)
print(person)  # Person(name=Alice, age=25)

# 测试类型检查
try:
    person.age = "twenty-five"  # 抛出TypeError
except TypeError as e:
    print(f"Type error: {e}")

# 测试非数据描述符
# 注意：直接设置实例属性会覆盖非数据描述符
person.greeting = "Hello from instance"
print(person.greeting)  # Hello from instance（实例属性）

# 但如果删除实例属性，会回退到描述符
del person.greeting
print(person.greeting)  # NonDataDescriptor.__get__ called for greeting

# 高级描述符：验证和转换描述符
class ValidatedProperty:
    """带验证和转换的描述符"""
    
    def __init__(self, validator=None, converter=None):
        self.validator = validator
        self.converter = converter
    
    def __set_name__(self, owner, name):
        self.name = name
        self.storage_name = f'_{name}'
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.storage_name, None)
    
    def __set__(self, obj, value):
        # 转换值
        if self.converter:
            value = self.converter(value)
        
        # 验证值
        if self.validator and not self.validator(value):
            raise ValueError(f"Invalid value for {self.name}: {value}")
        
        setattr(obj, self.storage_name, value)

# 使用验证描述符
class Product:
    price = ValidatedProperty(
        validator=lambda x: x > 0,
        converter=float
    )
    
    name = ValidatedProperty(
        validator=lambda x: isinstance(x, str) and len(x.strip()) > 0,
        converter=str.strip
    )
    
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

try:
    product = Product("  Widget  ", "29.99")  # 价格字符串会被转换为浮点数
    print(f"Product: {product.name}, Price: ${product.price}")
    # 输出: Product: Widget, Price: $29.99
    
    # 无效价格
    # product.price = -10  # ValueError
except ValueError as e:
    print(f"Error: {e}")

# 描述符在标准库中的应用：property、staticmethod、classmethod
class CachedProperty:
    """类似functools.cached_property的描述符"""
    
    def __init__(self, func):
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__
    
    def __set_name__(self, owner, name):
        if self.attrname is None:
            self.attrname = name
        elif self.attrname != name:
            raise TypeError(
                "Cannot assign the same CachedProperty to two different names."
            )
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.attrname is None:
            raise TypeError(
                "Cannot use CachedProperty instance without calling __set_name__."
            )
        
        # 计算值并缓存
        val = self.func(obj)
        setattr(obj, self.attrname, val)  # 设置实例属性，覆盖描述符
        return val

# 使用CachedProperty
class ExpensiveComputation:
    """演示缓存属性的类"""
    
    @CachedProperty
    def computed_data(self):
        """计算密集型操作"""
        print("Performing expensive computation...")
        import time
        time.sleep(1)  # 模拟耗时计算
        return {"result": 42}
    
    def __init__(self):
        pass

# 测试缓存效果
obj = ExpensiveComputation()
print("First access:")
data1 = obj.computed_data  # 触发计算
print(f"Data: {data1}")

print("\nSecond access:")
data2 = obj.computed_data  # 直接从缓存读取，不会再次计算
print(f"Data: {data2}")
print(f"Same object: {data1 is data2}")  # True
```

## 4. 上下文管理器的高级模式

```python
from contextlib import contextmanager, asynccontextmanager, ContextDecorator
from typing import Generator, AsyncGenerator, Optional, Any
import time
import asyncio
from functools import wraps

class TransactionalContext:
    """事务上下文管理器"""
    
    def __init__(self, connection):
        self.connection = connection
        self.transaction = None
    
    def __enter__(self):
        print("Starting transaction")
        self.transaction = self.connection.begin()
        return self.transaction
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print(f"Rolling back transaction due to: {exc_val}")
            self.transaction.rollback()
            # 不抑制异常，返回False
            return False
        else:
            print("Committing transaction")
            self.transaction.commit()
            return True

class ResourcePool:
    """资源池上下文管理器"""
    
    def __init__(self, factory, max_size=10):
        self.factory = factory
        self.pool = []
        self.max_size = max_size
        self.in_use = set()
    
    def acquire(self):
        """获取资源"""
        if self.pool:
            resource = self.pool.pop()
        else:
            resource = self.factory()
        self.in_use.add(resource)
        return resource
    
    def release(self, resource):
        """释放资源"""
        if resource in self.in_use:
            self.in_use.remove(resource)
            if len(self.pool) < self.max_size:
                self.pool.append(resource)
            else:
                self._destroy_resource(resource)
    
    def _destroy_resource(self, resource):
        """销毁资源"""
        if hasattr(resource, 'close'):
            resource.close()
    
    def __enter__(self):
        self.resource = self.acquire()
        return self.resource
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release(self.resource)

# 使用示例
class DatabaseConnection:
    """模拟数据库连接"""
    
    def __init__(self, db_name):
        self.db_name = db_name
        print(f"Creating connection to {db_name}")
    
    def execute(self, query):
        print(f"Executing: {query}")
    
    def close(self):
        print(f"Closing connection to {self.db_name}")
    
    def begin(self):
        print("Beginning transaction")
        return self
    
    def commit(self):
        print("Committing transaction")
    
    def rollback(self):
        print("Rolling back transaction")

# 使用资源池
connection_pool = ResourcePool(
    lambda: DatabaseConnection("mydb"),
    max_size=5
)

# 多个上下文管理器的组合使用
@contextmanager
def managed_resource(resource_name: str):
    """基础资源管理器"""
    print(f"Acquiring {resource_name}")
    resource = {"name": resource_name, "status": "active"}
    try:
        yield resource
    except Exception as e:
        print(f"Error with {resource_name}: {e}")
        resource["status"] = "error"
        raise
    finally:
        print(f"Releasing {resource_name}")
        resource["status"] = "released"

@contextmanager
def performance_monitor(operation_name: str):
    """性能监控上下文管理器"""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        duration = end_time - start_time
        print(f"{operation_name} took {duration:.4f} seconds")

@contextmanager
def exception_handler(exception_type=Exception, default_value=None):
    """异常处理上下文管理器"""
    try:
        yield
    except exception_type as e:
        print(f"Handled exception: {e}")
        return default_value

# 组合使用多个上下文管理器
def complex_operation():
    with performance_monitor("Complex Operation"):
        with managed_resource("database") as db:
            print(f"Using {db['name']}")
            with managed_resource("cache") as cache:
                print(f"Using {cache['name']}")
                # 模拟操作
                time.sleep(0.1)

# 上下文管理器工厂
class ContextManagerFactory:
    """上下文管理器工厂"""
    
    @staticmethod
    def create_timeout(timeout_seconds: float):
        """创建超时上下文管理器"""
        @contextmanager
        def timeout_context():
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
            
            # 设置信号处理程序（仅Unix）
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout_seconds))
            
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return timeout_context()
    
    @staticmethod
    def create_retry(max_attempts: int = 3, delay: float = 1.0):
        """创建重试上下文管理器"""
        @contextmanager
        def retry_context():
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    yield attempt
                    return  # 成功则退出
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                        time.sleep(delay)
            
            if last_exception:
                raise last_exception
        
        return retry_context()

# 可重入的上下文管理器
class ReentrantLock:
    """可重入锁上下文管理器"""
    
    def __init__(self):
        self._lock = False
        self._count = 0
    
    def __enter__(self):
        self._count += 1
        if not self._lock:
            self._lock = True
            print("Lock acquired")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._count -= 1
        if self._count == 0:
            self._lock = False
            print("Lock released")

# 异步上下文管理器（Python 3.6+）
class AsyncDatabaseConnection:
    """异步数据库连接"""
    
    def __init__(self, db_name):
        self.db_name = db_name
    
    async def __aenter__(self):
        print(f"Async connecting to {self.db_name}")
        await asyncio.sleep(0.1)  # 模拟连接时间
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"Async disconnecting from {self.db_name}")
        await asyncio.sleep(0.1)  # 模拟断开连接
        return False
    
    async def execute(self, query):
        print(f"Async executing: {query}")
        await asyncio.sleep(0.05)

@asynccontextmanager
async def async_resource_pool(factory, max_size=5):
    """异步资源池"""
    pool = []
    
    async def get_resource():
        if pool:
            return pool.pop()
        return await factory()
    
    async def release_resource(resource):
        if len(pool) < max_size:
            pool.append(resource)
        else:
            await resource.close()
    
    resource = await get_resource()
    try:
        yield resource
    finally:
        await release_resource(resource)

# 使用异步上下文管理器
async def async_example():
    async with AsyncDatabaseConnection("async_db") as conn:
        await conn.execute("SELECT *