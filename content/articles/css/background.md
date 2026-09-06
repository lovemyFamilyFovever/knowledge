---
outline: [1,3]
head:
  - - meta
    - name: description
      content: css background 
  - - meta
    - name: keywords
      content: css background 
tags: [CSS]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/css/background.md"
---

在 CSS 中，使用 `background` 或 `background-image` 设置背景图片时，可以通过多个相关属性精细控制背景的显示方式。以下是**所有与背景图片相关的 CSS 属性**及其作用：

------

### ✅ 1. `background-image`

设置背景图片（可叠加多张）。

```css
background-image: url('image.jpg');
background-image: url('img1.png'), url('img2.jpg'); /* 多重背景 */
```

> ⚠️ 注意：如果只写 `background: url(...)`，会**重置其他 background 子属性为默认值**！

------

### ✅ 2. `background-repeat`

控制图片是否/如何平铺。

```css
background-repeat: repeat;     /* 默认：水平+垂直平铺 */
background-repeat: no-repeat;  /* 不平铺 */
background-repeat: repeat-x;   /* 仅水平平铺 */
background-repeat: repeat-y;   /* 仅垂直平铺 */
background-repeat: space;      /* 平铺但不裁剪，保持完整图像 */
background-repeat: round;      /* 缩放图像以适应容器，无间隙 */
```

------

### ✅ 3. `background-position`

设置图片起始位置。

```css
background-position: left top;        /* 关键词 */
background-position: 20px 50px;       /* 绝对值 */
background-position: 50% 50%;         /* 百分比（默认 center） */
background-position: center;          /* 简写（等价于 50% 50%） */
background-position: right 20px bottom 10px; /* 新语法（CSS3） */
```

------

### ✅ 4. `background-size`

控制图片尺寸。

```css
background-size: auto;        /* 默认：原始尺寸 */
background-size: cover;       /* 缩放覆盖整个容器（可能裁剪） */
background-size: contain;     /* 完整显示图片（可能留空） */
background-size: 100px 200px; /* 固定宽高 */
background-size: 50% auto;    /* 宽度50%，高度自适应 */
```

------

### ✅ 5. `background-attachment`

控制滚动时背景的行为。

```css
background-attachment: scroll;  /* 默认：随内容滚动 */
background-attachment: fixed;   /* 背景固定（视口固定） */
background-attachment: local;   /* 背景随元素内容滚动（如 textarea 内部） */
```

------

### ✅ 6. `background-origin`

定义 `background-position` 的参考区域（**不影响绘制区域**）。

```css
background-origin: border-box; /* 从边框外侧开始定位（默认） */
background-origin: padding-box; /* 从内边距开始定位（常用） */
background-origin: content-box; /* 从内容区开始定位 */
```

------

### ✅ 7. `background-clip`

定义背景的**绘制区域**（即在哪里显示）。

```css
background-clip: border-box;  /* 默认：绘制到边框外沿 */
background-clip: padding-box; /* 绘制到内边距外沿 */
background-clip: content-box; /* 仅在内容区内绘制 */
background-clip: text;        /* 背景仅在文字内显示（需配合 -webkit-text-fill-color: transparent） */
```

> 💡 `background-clip: text` 示例：
>
> ```css
> h1 {
>   background-image: linear-gradient(red, blue);
>   -webkit-background-clip: text;
>   background-clip: text;
>   color: transparent;
> }
> ```

------

### ✅ 8. `background-color`

虽然不是图片属性，但它是背景的一部分（图片透明区域会显示底色）。

```css
background-color: #f0f0f0;
```

------

### 🧩 9. 简写属性：`background`

可以一次性设置所有背景属性（顺序不严格，但推荐按规范写）：

```css
background: [color] [image] [repeat] [position / size] [origin] [clip] [attachment];
```

#### ✅ 正确示例：

```css
/* 常见用法 */
background: #eee url(bg.jpg) no-repeat center/cover;

/* 完整写法（含 origin/clip） */
background: url(bg.png) no-repeat center/contain padding-box content-box fixed;
```

> ⚠️ 注意：`position / size` 必须用 `/` 连接，且必须同时出现才能用简写。

------

### 🔒 浏览器兼容性提示

| 属性                                    | 兼容性               |
| --------------------------------------- | -------------------- |
| `background-clip: text`                 | 需加 `-webkit-` 前缀 |
| `background-origin` / `background-clip` | IE9+                 |
| 多重背景                                | IE9+                 |
| `space` / `round` (repeat)              | IE10+                |

------

### ✅ 最佳实践建议

- **优先使用简写**（如 `background: no-repeat center/cover url(...)`），简洁高效；
- 若需动态修改某一项（如 JS 改变 `background-position`），**不要用简写**，否则会覆盖其他值；
- 背景图尽量用 **`cover` 或 `contain`** 保证响应式；
- 避免在 `` 上用背景图，语义化差且 SEO 不友好。