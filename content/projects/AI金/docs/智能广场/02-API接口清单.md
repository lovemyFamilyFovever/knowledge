# 智能广场 API 接口清单
> 最后更新：2026-08-26

本文以当前 `server/modules/plaza/` 控制器为准。除明确标注公开的接口外，均使用 `Authorization: Bearer <sessionToken>` 登录态；飞书环境的前端请求还需携带 `x-suda-csrf-token`。

## 一、帖子、搜索与互动

| 方法 | 路径 | 登录 | 说明 |
|---|---|---|---|
| GET | `/api/plaza/posts` | 必须 | 列表或单帖；参数：`page`、`pageSize`、`newsId`、`feed=recommended/latest/following`、`refreshSeed` |
| GET | `/api/plaza/search` | 必须 | 搜索；参数：`q`、`page`、`pageSize`、`type=all/video/image/article`、`sort=relevance/latest` |
| GET | `/api/plaza/search/suggestions` | 必须 | 输入联想；参数：`q` |
| POST | `/api/plaza/posts` | 必须 | 发布帖子；图像上传最多 9 张、每张最多 2MB |
| DELETE | `/api/plaza/posts/:newsId` | 必须 | 删除本人帖子 |
| PATCH | `/api/plaza/posts/:newsId/visibility` | 必须 | 修改可见范围：`public`、`private`、`friends` |
| GET / POST | `/api/plaza/posts/:newsId/comments` | 必须 | 获取评论 / 发表评论或回复 |
| POST | `/api/plaza/posts/:newsId/like` | 必须 | 点赞/取消点赞 |
| POST | `/api/plaza/posts/:newsId/favorite` | 必须 | 收藏/取消收藏 |
| POST | `/api/plaza/comments/:commentId/like` | 必须 | 评论点赞/取消点赞 |
| POST | `/api/plaza/members/:memberCode/follow` | 必须 | 关注/取消关注 |
| GET | `/api/plaza/share/:newsId` | 必须 | 分享预览；前端分享页虽免登录，当前 API 仍受全局登录守卫保护 |
| GET | `/api/plaza/images/:rowId/:index` | 公开 | 图片读取，`index` 为 0–8 |

## 二、个人、用户主页与通知

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/plaza/me/posts`、`/me/favorites`、`/me/likes`、`/me/history` | 我的帖子、收藏、点赞、观看历史 |
| GET | `/api/plaza/me/follows`、`/me/followers` | 我的关注、粉丝 |
| GET | `/api/plaza/users/:memberCode`、`/users/:memberCode/posts` | 用户资料与用户帖子；必须登录 |
| POST | `/api/plaza/notifications/query` | 按分类查询聚合通知 |
| POST | `/api/plaza/notifications/unread-counts`、`/interaction-stats` | 获取未读数、互动统计 |
| POST | `/api/plaza/notifications/read`、`/read-category` | 标记单卡片或某分类已读 |

个人列表分页的 `page` 默认 0、`pageSize` 默认 10，最大 50。

## 三、供需挂单

| 方法 | 路径 | 说明 |
|---|---|---|
| POST / GET | `/api/plaza/demands` | 创建 / 筛选供应挂单 |
| GET | `/api/plaza/demands/mine`、`/active`、`/by-material` | 我的、有效、按材质的挂单 |
| GET / PUT / DELETE | `/api/plaza/demands/:id` | 查看 / 编辑 / 删除本人挂单 |
| POST | `/api/plaza/demands/:id/match` | 智能匹配 |
| POST | `/api/plaza/demands/analyze` | 解析挂单文本参数 |

## 四、AI 搜索辅助

以下接口实现于 `server/modules/ai/ai.controller.ts`，由广场搜索页调用：

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/ai/plaza-search-recommend` | 生成“猜你想搜” |
| POST | `/api/ai/plaza-search-insight` | 总结搜索结果 |
| POST | `/api/ai/plaza-search-insight/stream` | SSE 流式输出搜索结果总结 |

这些接口只读取公开帖子及相关画像、行为数据，不写入广场业务表。
