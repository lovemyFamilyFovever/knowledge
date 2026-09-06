---
title: "WebAssembly完全指南"
tags: []
source: "baike"
source_path: "技术文章 / Web开发框架"
collected: "2026-09-05"
status: "imported"
---

# WebAssembly完全指南

# WebAssembly 完全指南

## 1. WebAssembly 是什么？

WebAssembly（简称 Wasm）是一种基于栈的虚拟机的二进制指令格式，设计为可移植、体积小、加载快并且可以安全地执行。它是 W3C 标准，由主流浏览器厂商共同支持。

### 1.1 指令集架构

Wasm 采用基于栈的指令集架构（与基于寄存器的 x86 不同）。程序通过压栈、出栈完成运算：

```wasm
;; 计算 (2 + 3) * 4
i32.const 2    ;; 将 2 压栈
i32.const 3    ;; 将 3 压栈
i32.add        ;; 弹出两个值，相加后压入结果 5
i32.const 4    ;; 将 4 压栈
i32.mul        ;; 弹出 5 和 4，相乘后压入 20
```

Wasm 支持四种基本数值类型：
- `i32`：32 位整数
- `i64`：64 位整数
- `f32`：32 位浮点数
- `f64`：64 位浮点数

指令集包含约 200 条指令，涵盖算术、比较、控制流、内存操作等：

```wasm
;; 控制流示例：if-else
(if (result i32)
  (i32.gt_s (local.get $x) (i32.const 0))
  (then (i32.const 1))
  (else (i32.const 0))
)
```

### 1.2 线性内存模型

Wasm 使用线性内存（Linear Memory）—— 一个连续、可调整大小的字节数组。所有内存访问都是通过显式的 load/store 指令：

```wasm
;; 将值 42 存储到地址 0
i32.const 0      ;; 地址
i32.const 42     ;; 值
i32.store         ;; 存储操作

;; 从地址 0 读取值
i32.const 0
i32.load          ;; 压入 42
```

内存以 64KB 页为单位增长：

```wasm
;; 初始 1 页（64KB），最多增长到 10 页
(memory (export "memory") 1 10)
```

**安全特性**：Wasm 运行时自动进行边界检查，防止内存越界访问。

### 1.3 模块系统

Wasm 程序被组织为模块（Module），包含：
- **类型节（Type Section）**：函数签名
- **函数节（Function Section）**：函数体
- **内存节（Memory Section）**：内存定义
- **表节（Table Section）**：用于间接调用的函数引用表
- **导入/导出节**：与宿主环境交互

```wasm
(module
  ;; 导入 JavaScript 函数
  (import "console" "log" (func $log (param i32)))
  
  ;; 导出函数供外部调用
  (func (export "add") (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    i32.add
  )
  
  ;; 导出内存
  (memory (export "memory") 1)
)
```

**实例化过程**：
```javascript
// 加载、编译、实例化
const response = await fetch('module.wasm');
const bytes = await response.arrayBuffer();
const { instance } = await WebAssembly.instantiate(bytes, {
  console: { log: (arg) => console.log(arg) }
});

console.log(instance.exports.add(3, 5)); // 8
```

## 2. Wasm 与 JavaScript 的互操作

### 2.1 JavaScript 调用 Wasm

Wasm 模块导出的函数可直接被 JavaScript 调用：

```javascript
// 异步编译和实例化
async function loadWasm() {
  const response = await fetch('math.wasm');
  const bytes = await response.arrayBuffer();
  
  const results = await WebAssembly.instantiate(bytes, {
    env: {
      memory: new WebAssembly.Memory({ initial: 1 }),
      log: (value) => console.log(`Wasm says: ${value}`)
    }
  });
  
  const { instance } = results;
  
  // 直接调用 Wasm 函数
  const sum = instance.exports.add(10, 20);
  console.log(`Sum: ${sum}`);
  
  // 调用高性能函数
  const matrixResult = instance.exports.matrixMultiply(
    matrixA, matrixB, 100
  );
  
  return instance;
}
```

### 2.2 Wasm 调用 JavaScript

通过导入函数，Wasm 可以调用 JavaScript：

```wasm
(module
  ;; 导入 JavaScript 函数
  (import "js" "fetch" (func $fetch (param i32 i32) (result i32)))
  (import "js" "render" (func $render (param i32 i32 i32)))
  
  (func (export "processData") (param $ptr i32) (param $len i32)
    ;; 调用 JS 的 fetch 函数获取数据
    local.get $ptr
    local.get $len
    call $fetch
    
    ;; 处理数据...
    
    ;; 调用 JS 的 render 函数
    i32.const 0  ;; x
    i32.const 0  ;; y
    i32.const 100 ;; width
    call $render
  )
)
```

对应的 JavaScript 代码：
```javascript
const importObject = {
  js: {
    fetch: async (ptr, len) => {
      // 从 Wasm 内存读取数据
      const memory = instance.exports.memory;
      const url = readStringFromMemory(memory, ptr, len);
      
      const response = await fetch(url);
      const data = await response.arrayBuffer();
      
      // 将数据写入 Wasm 内存
      return writeToMemory(memory, data);
    },
    
    render: (x, y, width) => {
      const canvas = document.getElementById('canvas');
      const ctx = canvas.getContext('2d');
      // 从 Wasm 内存读取像素数据并渲染
      renderFromWasmMemory(ctx, x, y, width);
    }
  }
};
```

### 2.3 内存共享与数据传输

**字符串处理**：
```javascript
// 将 JS 字符串写入 Wasm 内存
function writeString(memory, string, offset) {
  const buffer = new Uint8Array(memory.buffer);
  const bytes = new TextEncoder().encode(string);
  
  // 写入长度（4字节）
  const lengthBytes = new Uint8Array(4);
  new DataView(lengthBytes.buffer).setUint32(0, bytes.length, true);
  buffer.set(lengthBytes, offset);
  
  // 写入字符串内容
  buffer.set(bytes, offset + 4);
  
  return offset;
}

// 从 Wasm 内存读取字符串
function readString(memory, offset) {
  const buffer = new Uint8Array(memory.buffer);
  
  // 读取长度
  const length = new DataView(buffer.buffer, offset, 4).getUint32(0, true);
  
  // 读取字符串
  const bytes = buffer.slice(offset + 4, offset + 4 + length);
  return new TextDecoder().decode(bytes);
}
```

**大数组传输**：
```javascript
// 批量传输大量数据到 Wasm
function sendLargeArray(instance, array) {
  const memory = instance.exports.memory;
  const pointer = instance.exports.allocate(array.length * 4);
  
  // 创建视图直接操作 Wasm 内存
  const memoryView = new Float64Array(
    memory.buffer, 
    pointer, 
    array.length
  );
  
  // 批量复制（比逐个写入快得多）
  memoryView.set(array);
  
  // 调用 Wasm 处理数据
  const result = instance.exports.processData(pointer, array.length);
  
  // 读取结果
  const resultArray = new Float64Array(memory.buffer, result, array.length);
  
  // 释放内存
  instance.exports.deallocate(pointer, array.length * 4);
  
  return resultArray;
}
```

### 2.4 高性能交互模式

**SharedArrayBuffer 用于 Worker 间通信**：
```javascript
// 主线程
const sharedMemory = new WebAssembly.Memory({
  initial: 1,
  maximum: 10,
  shared: true
});

const worker = new Worker('worker.js');
worker.postMessage({ memory: sharedMemory });

// Worker 线程
self.onmessage = async (e) => {
  const memory = e.data.memory;
  
  const response = await fetch('processor.wasm');
  const bytes = await response.arrayBuffer();
  
  const { instance } = await WebAssembly.instantiate(bytes, {
    env: { memory }
  });
  
  // 现在主线程和 Worker 共享同一块内存
  instance.exports.processInParallel();
};
```

## 3. 用 Rust/C++/Go 编写 Wasm

### 3.1 Rust → Wasm

**安装工具链**：
```bash
# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 添加 wasm32 目标
rustup target add wasm32-unknown-unknown

# 安装 wasm-pack（用于构建、测试、发布）
cargo install wasm-pack
```

**基础示例**：
```rust
// src/lib.rs
use wasm_bindgen::prelude::*;

// 导出函数到 JavaScript
#[wasm_bindgen]
pub fn fibonacci(n: u32) -> u64 {
    if n == 0 { return 0; }
    if n == 1 { return 1; }
    
    let mut a: u64 = 0;
    let mut b: u64 = 1;
    
    for _ in 2..=n {
        let temp = b;
        b = a + b;
        a = temp;
    }
    
    b
}

// 复杂数据结构
#[wasm_bindgen]
pub struct ImageProcessor {
    width: u32,
    height: u32,
    data: Vec<u8>,
}

#[wasm_bindgen]
impl ImageProcessor {
    #[wasm_bindgen(constructor)]
    pub fn new(width: u32, height: u32) -> ImageProcessor {
        ImageProcessor {
            width,
            height,
            data: vec![0; (width * height * 4) as usize],
        }
    }
    
    #[wasm_bindgen]
    pub fn apply_grayscale(&mut self) {
        for i in (0..self.data.len()).step_by(4) {
            let r = self.data[i] as f32;
            let g = self.data[i + 1] as f32;
            let b = self.data[i + 2] as f32;
            
            let gray = 0.299 * r + 0.587 * g + 0.114 * b;
            let gray = gray as u8;
            
            self.data[i] = gray;
            self.data[i + 1] = gray;
            self.data[i + 2] = gray;
        }
    }
    
    #[wasm_bindgen]
    pub fn get_data_ptr(&self) -> *const u8 {
        self.data.as_ptr()
    }
}
```

**Cargo.toml**：
```toml
[package]
name = "wasm-example"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
wasm-bindgen = "0.2"
console_error_panic_hook = "0.1"

[profile.release]
opt-level = 3
lto = true
```

**构建**：
```bash
# 开发构建
wasm-pack build --target web

# 生产构建（优化）
wasm-pack build --target web --release

# 生成 npm 包
wasm-pack build --target nodejs
```

**使用示例**：
```javascript
import init, { fibonacci, ImageProcessor } from './pkg/wasm_example.js';

async function main() {
  await init();
  
  console.log(fibonacci(40)); // 102334155
  
  const processor = new ImageProcessor(1920, 1080);
  processor.apply_grayscale();
  const dataPtr = processor.get_data_ptr();
  
  // 从 Wasm 内存读取像素数据
  const memory = processor.__wbg_ptr;
  const data = new Uint8ClampedArray(
    memory.buffer, 
    dataPtr, 
    1920 * 1080 * 4
  );
  
  // 渲染到 canvas
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  const imageData = new ImageData(data, 1920, 1080);
  ctx.putImageData(imageData, 0, 0);
}

main();
```

### 3.2 C++ → Wasm

**使用 Emscripten**：
```bash
# 安装 Emscripten SDK
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh
```

**C++ 代码**：
```cpp
// image_processor.cpp
#include <emscripten/bind.h>
#include <vector>
#include <cmath>
#include <algorithm>

using namespace emscripten;

class ImageProcessor {
private:
    std::vector<uint8_t> data;
    int width;
    int height;
    
public:
    ImageProcessor(int w, int h) : width(w), height(h) {
        data.resize(w * h * 4, 0);
    }
    
    void setPixel(int x, int y, uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
        int index = (y * width + x) * 4;
        data[index] = r;
        data[index + 1] = g;
        data[index + 2] = b;
        data[index + 3] = a;
    }
    
    // 高斯模糊（CPU密集型任务）
    void gaussianBlur(int radius) {
        std::vector<uint8_t> temp(data.size());
        double sigma = radius / 3.0;
        int size = 2 * radius + 1;
        std::vector<double> kernel(size * size);
        
        // 生成高斯核
        double sum = 0;
        for (int i = -radius; i <= radius; i++) {
            for (int j = -radius; j <= radius; j++) {
                double value = exp(-(i*i + j*j)/(2*sigma*sigma));
                kernel[(i+radius)*size + (j+radius)] = value;
                sum += value;
            }
        }
        
        // 归一化
        for (auto& val : kernel) {
            val /= sum;
        }
        
        // 应用卷积
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                double r = 0, g = 0, b = 0;
                
                for (int ky = -radius; ky <= radius; ky++) {
                    for (int kx = -radius; kx <= radius; kx++) {
                        int px = std::clamp(x + kx, 0, width-1);
                        int py = std::clamp(y + ky, 0, height-1);
                        int index = (py * width + px) * 4;
                        
                        double weight = kernel[(ky+radius)*size + (kx+radius)];
                        r += data[index] * weight;
                        g += data[index+1] * weight;
                        b += data[index+2] * weight;
                    }
                }
                
                int idx = (y * width + x) * 4;
                temp[idx] = std::clamp((int)r, 0, 255);
                temp[idx+1] = std::clamp((int)g, 0, 255);
                temp[idx+2] = std::clamp((int)b, 0, 255);
                temp[idx+3] = data[idx+3];
            }
        }
        
        data = temp;
    }
    
    // SIMD 优化版本
    void gaussianBlurSIMD(int radius) {
        // 使用 Emscripten SIMD intrinsics
        // 需要编译时启用 -msimd128
        #ifdef __wasm_simd128
        // SIMD 优化实现...
        #endif
    }
    
    val getData() {
        // 返回 JavaScript TypedArray 视图
        return val(typed_memory_view(data.size(), data.data()));
    }
};

// 绑定到 JavaScript
EMSCRIPTEN_BINDINGS(image_processor) {
    class_<ImageProcessor>("ImageProcessor")
        .constructor<int, int>()
        .function("setPixel", &ImageProcessor::setPixel)
        .function("gaussianBlur", &ImageProcessor::gaussianBlur)
        .function("gaussianBlurSIMD", &ImageProcessor::gaussianBlurSIMD)
        .function("getData", &ImageProcessor::getData);
}
```

**编译命令**：
```bash
# 基础编译
emcc image_processor.cpp -o image_processor.js \
  --bind \
  -O3 \
  -s WASM=1 \
  -s MODULARIZE=1 \
  -s EXPORT_NAME="ImageProcessorModule"

# 启用 SIMD 优化
emcc image_processor.cpp -o image_processor_simd.js \
  --bind \
  -O3 \
  -s WASM=1 \
  -msimd128 \
  -s SIMD=1

# 多线程支持
emcc image_processor.cpp -o image_processor_mt.js \
  --bind \
  -O3 \
  -s WASM=1 \
  -s USE_PTHREADS=1 \
  -s PTHREAD_POOL_SIZE=4
```

**HTML 使用**：
```html
<!DOCTYPE html>
<html>
<head>
    <title>C++ Wasm Image Processor</title>
    <script src="image_processor.js"></script>
</head>
<body>
    <canvas id="canvas" width="800" height="600"></canvas>
    <script>
        ImageProcessorModule().then(Module => {
            const processor = new Module.ImageProcessor(800, 600);
            
            // 设置像素
            for (let x = 0; x < 800; x++) {
                for (let y = 0; y < 600; y++) {
                    processor.setPixel(x, y, x % 256, y % 256, 128, 255);
                }
            }
            
            // 应用高斯模糊（计算密集型）
            const start = performance.now();
            processor.gaussianBlur(5);
            const end = performance.now();
            console.log(`Blur took ${end - start} ms`);
            
            // 获取处理后的数据
            const data = processor.getData();
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const imageData = new ImageData(
                new Uint8ClampedArray(data), 
                800, 
                600
            );
            ctx.putImageData(imageData, 0, 0);
        });
    </script>
</body>
</html>
```

### 3.3 Go → Wasm

**Go 代码**：
```go
// main.go
package main

import (
    "fmt"
    "math"
    "syscall/js"
)

// 计算圆周率（蒙特卡洛方法）
func estimatePi(numSamples int) float64 {
    insideCircle := 0
    
    for i := 0; i < numSamples; i++ {
        x := js.Global().Get("Math").Call("random").Float()
        y := js.Global().Get("Math").Call("random").Float()
        
        distance := math.Sqrt(x*x + y*y)
        if distance <= 1.0 {
            insideCircle++
        }
    }
    
    return 4.0 * float64(insideCircle) / float64(numSamples)
}

// 处理 JSON 数据
func processJSON(this js.Value, args []js.Value) interface{} {
    jsonStr := args[0].String()
    
    var data map[string]interface{}
    err := json.Unmarshal([]byte(jsonStr), &data)
    if err != nil {
        return js.ValueOf(map[string]interface{}{
            "error": err.Error(),
        })
    }
    
    // 处理数据...
    result := make(map[string]interface{})
    result["processed"] = true
    result["count"] = len(data)
    
    return js.ValueOf(result)
}

// 并发处理（Go goroutines 在 Wasm 中仍然可用）
func parallelProcess(this js.Value, args []js.Value) interface{} {
    jsData := args[0]
    length := jsData.Length()
    
    // 创建结果通道
    resultChan := make(chan float64, length)
    
    // 启动多个 goroutine 并行处理
    for i := 0; i < length; i++ {
        go func(index int) {
            value := jsData.Index(index).Float()
            resultChan <- math.Sqrt(value) * math.Sin(value)
        }(i)
    }
    
    // 收集结果
    results := make([]interface{}, length)
    for i := 0; i < length; i++ {
        results[i] = <-resultChan
    }
    
    return js.ValueOf(results)
}

func main() {
    // 注册函数到 JavaScript
    js.Global().Set("estimatePi", js.FuncOf(func(this js.Value, args []js.Value) interface{} {
        numSamples := args[0].Int()
        return estimatePi(numSamples)
    }))
    
    js.Global().Set("processJSON", js.FuncOf(processJSON))
    js.Global().Set("parallelProcess", js.FuncOf(parallelProcess))
    
    // 保持程序运行
    select {}
}
```

**构建命令**：
```bash
# 设置 GOOS 和 GOARCH
export GOOS=js
export GOARCH=wasm

# 编译
go build -o main.wasm main.go

# 复制 wasm_exec.js（Go 提供的胶水代码）
cp "$(go env GOROOT)/misc/wasm/wasm_exec.js" .
```

**HTML 使用**：
```html
<!DOCTYPE html>
<html>
<head>
    <title>Go Wasm Example</title>
    <script src="wasm_exec.js"></script>
</head>
<body>
    <script>
        async function main() {
            const go = new Go();
            const result = await WebAssembly.instantiateStreaming(
                fetch("main.wasm"), 
                go.importObject
            );
            go.run(result.instance);
            
            // 调用 Go 函数
            const pi = estimatePi(10000000);
            console.log(`Estimated π: ${pi}`);
            
            // 并发处理示例
            const data = new Float64Array([1, 4, 9, 16, 25]);
            const results = parallelProcess(data);
            console.log(results);
        }
        
        main();
    </script>
</body>
</html>
```

## 4. WASI（WebAssembly System Interface）

WASI 是 WebAssembly 的标准化系统接口，允许 Wasm 程序安全地访问操作系统功能。

### 4.1 WASI 概念

WASI 的核心原则：
1. **能力安全性**：程序只能访问被明确授予的能力
2. **可移植性**：相同的 Wasm 二进制可在不同实现中运行
3. **沙箱隔离**：每个程序运行在自己的沙箱中

### 4.2 基础 WASI 应用

**Rust 示例**：
```rust
// main.rs
use std::env;
use std::fs;
use std::io::{self, Read, Write};

fn main() -> io::Result<()> {
    // 获取命令行参数
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: {} <filename>", args[0]);
        std::process::exit(1);
    }
    
    let filename = &args[1];
    
    // 读取文件（需要 fs 权限）
    let content = fs::read_to_string(filename)?;
    
    // 写入标准输出
    io::stdout().write_all(content.as_bytes())?;
    
    // 环境变量访问
    if let Ok(rust_log) = env::var("RUST_LOG") {
        eprintln!("Log level: {}", rust_log);
    }
    
    // 当前时间
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs();
    
    println!("Current timestamp: {}", now);
    
    Ok(())
}
```

**构建与运行**：
```bash
# 编译为 WASI 目标
rustup target add wasm32-wasi
cargo build --target wasm32-wasi --release

# 使用 Wasmtime 运行
wasmtime run --dir=. --env=RUST_LOG=debug target/wasm32-wasi/release/wasi-example.wasm input.txt

# 使用 WasmEdge 运行
wasmedge --dir=.:. target/wasm32-wasi/release/wasi-example.wasm input.txt
```

### 4.3 WASI 文件系统访问

```rust
use std::fs::{self, File};
use std::io::{Write, Read, BufReader, BufRead};

fn process_files() -> std::io::Result<()> {
    // 列出目录内容
    for entry in fs::read_dir(".")? {
        let entry = entry?;
        let metadata = entry.metadata()?;
        
        println!(
            "{}: {} bytes, modified: {:?}",
            entry.path().display(),
            metadata.len(),
            metadata.modified()?
        );
    }
    
    // 读取大文件（带缓冲）
    let file = File::open("large_file.txt")?;
    let reader = BufReader::new(file);
    
    let mut line_count = 0;
    for line in reader.lines() {
        let line = line?;
        line_count += 1;
        // 处理每一行...
    }
    
    // 写入文件
    let mut output = File::create("output.txt")?;
    write!(output, "Processed {} lines", line_count)?;
    
    Ok(())
}
```

### 4.4 WASI 网络访问

WASI 目前网络支持有限，但正在通过 WASI Socket 提案扩展：

```rust
// 使用 wasi-common 的网络功能（实验性）
#[cfg(feature = "network")]
mod network {
    use std::net::{TcpListener, TcpStream};
    use std::io::{Read, Write};
    
    pub fn start_server() -> std::io::Result<()> {
        let listener = TcpListener::bind("0.0.0.0:8080")?;
        
        for stream in listener.incoming() {
            let mut stream = stream?;
            
            // 处理连接
            std::thread::spawn(move || {
                let mut buffer = [0; 1024];
                stream.read(&mut buffer).unwrap();
                
                let response = "HTTP/1.1 200 OK\r\n\r\nHello from Wasm!";
                stream.write(response.as_bytes()).unwrap();
                stream.flush().unwrap();
            });
        }
        
        Ok(())
    }
}
```

### 4.5 WASI 与宿主环境交互

**自定义宿主函数**：
```rust
// 宿主环境（Rust）
use wasmtime::*;
use wasmtime_wasi::WasiCtxBuilder;

fn main() -> anyhow::Result<()> {
    let engine = Engine::default();
    let module = Module::from_file(&engine, "module.wasm")?;
    
    // 创建 WASI 上下文
    let wasi = WasiCtxBuilder::new()
        .inherit_stdio()
        .args(&["arg1", "arg2"])?
        .env("KEY", "VALUE")?
        .build();
    
    // 添加自定义宿主函数
    let mut linker = Linker::new(&engine);
    wasmtime_wasi::add_to_linker(&mut linker, |s| s)?;
    
    // 自定义函数：获取系统信息
    linker.func_wrap("host", "get_system_info", |caller: Caller<'_, WasiCtx>| {
        let memory = caller.get_export("memory").unwrap().into_memory().unwrap();
        // 返回系统信息到 Wasm 内存
        Ok(42u32)
    })?;
    
    let mut store = Store::new(&engine, wasi);
    let instance = linker.instantiate(&mut store, &module)?;
    
    // 调用导出函数
    let start = instance.get_typed_func::<(), ()>(&mut store, "_start")?;
    start.call(&mut store, ())?;
    
    Ok(())
}
```

## 5. Wasm 在浏览器中的应用

### 5.1 图像处理

**使用 Rust + wasm-bindgen 处理图像**：
```rust
use wasm_bindgen::prelude::*;
use image::{ImageBuffer, Rgba, RgbaImage};
use imageproc::filter::gaussian_blur_f32;

#[wasm_bindgen]
pub struct ImageEditor {
    image: RgbaImage,
}

#[wasm_bindgen]
impl ImageEditor {
    #[wasm_bindgen(constructor)]
    pub fn new(width: u32, height: u32) -> Self {
        ImageEditor {
            image: ImageBuffer::new(width, height),
        }
    }
    
    // 从 JavaScript 加载图像数据
    #[wasm_bindgen]
    pub fn load_from_data(&mut self, data: &[u8], width: u32, height: u32) {
        self.image = ImageBuffer::from_raw(width, height, data.to_vec())
            .expect("Invalid image data");
    }
    
    // 获取图像数据指针
    #[wasm_bindgen]
    pub fn data_ptr(&self) -> *const u8 {
        self.image.as_raw().as_ptr()
    }
    
    // 应用多种滤镜
    #[wasm_bindgen]
    pub fn apply_filter(&mut self, filter_type: &str, intensity: f32) {
        match filter_type {
            "blur" => {
                self.image = gaussian_blur_f32(&self.image, intensity);
            },
            "brightness" => {
                for pixel in self.image.pixels_mut() {
                    let [r, g, b, a] = pixel.0;
                    *pixel = Rgba([
                        (r as f32 * intensity).min(255.0) as u8,
                        (g as f32 * intensity).min(255.0) as u8,
                        (b as f32 * intensity).min(255.0) as u8,
                        a,
                    ]);
                }
            },
            "sepia" => {
                for pixel in self.image.pixels_mut() {
                    let [r, g, b, a] = pixel.0;
                    let tr = 0.393 * r as f32 + 0.769 * g as f32 + 0.189 * b as f32;
                    let tg = 0.349 * r as f32 + 0.686 * g as f32 + 0.168 * b as f32;
                    let tb = 0.272 * r as f32 + 0.534 * g as f32 + 0.131 * b as f32;
                    
                    *pixel = Rgba([
                        tr.min(255.0) as u8,
                        tg.min(255.0) as u8,
                        tb.min(255.0) as u8,
                        a,
                    ]);
                }
            },
            _ => {}
        }
    }
    
    // 实时处理（低延迟）
    #[wasm_bindgen]
    pub fn realtime_process(&mut self, frame_data: &[u8], width: u32, height: u32) -> Vec<u8> {
        // 转换为灰度
        let mut result = Vec::with_capacity((width * height) as usize);
        
        for i in (0..frame_data.len()).step_by(4) {
            let r = frame_data[i] as f32;
            let g = frame_data[i + 1] as f32;
            let b = frame_data[i + 2] as f32;
            
            let gray = 0.299 * r + 0.587 * g + 0.114 * b;
            result.push(gray as u8);
        }
        
        result
    }
}
```

**JavaScript 集成**：
```javascript
class ImageProcessorApp {
    constructor() {
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.editor = null;
        this.video = null;
        this.isRealtime = false;
    }
    
    async init() {
        // 加载 Wasm 模块
        await init();
        this.editor = new ImageEditor(0, 0);
        
        this.setupControls();
        this.loadSampleImage();
    }
    
    setupControls() {
        // 滤镜选择器
        const filterSelect = document.getElementById('filter');
        filterSelect.addEventListener('change', () => {
            this.applyCurrentFilter();
        });
        
        // 强度滑块
        const intensitySlider = document.getElementById('intensity');
        intensitySlider.addEventListener('input', (e) => {
            this.applyCurrentFilter();
        });
        
        // 实时模式按钮
        const realtimeBtn = document.getElementById('realtime');
        realtimeBtn.addEventListener('click', () => {
            this.toggleRealtimeMode();
        });
    }
    
    applyCurrentFilter() {
        const filter = document.getElementById('filter').value;
        const intensity = parseFloat(document.getElementById('intensity').value);
        
        if (this.editor) {
            this.editor.apply_filter(filter, intensity);
            this.updateCanvas();
        }
    }
    
    updateCanvas() {
        const width = this.editor.width();
        const height = this.editor.height();
        
        // 从 Wasm 内存读取像素数据
        const dataPtr = this.editor.data_ptr();
        const memory = this.editor.__wbg_ptr.memory.buffer;
        const pixels = new Uint8ClampedArray(memory, dataPtr, width * height * 4);
        
        const imageData = new ImageData(pixels, width, height);
        this.ctx.putImageData(imageData, 0, 0);
    }
    
    toggleRealtimeMode() {
        this.isRealtime = !this.isRealtime;
        
        if (this.isRealtime) {
            this.startRealtimeProcessing();
        } else {
            this.stopRealtimeProcessing();
        }
    }
    
    startRealtimeProcessing() {
        this.video = document.createElement('video');
        this.video.srcObject = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });
        
        const processFrame = () => {
            if (!this.isRealtime) return;
            
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);