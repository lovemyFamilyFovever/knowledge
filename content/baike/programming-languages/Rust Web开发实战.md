---
title: "Rust Web开发实战"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Rust Web开发实战


> 📌 **导航**：本文是 **Rust Web开发实战** 词条，属于 programming-languages 术语集。相关枢纽：[[Go语言核心]]、[[Python高级编程完全指南]]、[[Rust系统编程入门到精通]]、[[Rust编程基础]]、[[TypeScript深入]]。

## Rust Web 开发实战指南

## 第一部分：Rust Web 生态概览

### Rust Web 框架三足鼎立

在Rust Web开发领域，三个主要框架占据了主导地位：Actix-web、Axum和Rocket。它们各自代表了不同的设计哲学和适用场景。

#### Actix-web：性能怪兽
Actix-web是最早成熟的Rust Web框架，以其卓越的性能著称。它基于Actor模型构建，使用Actix Actor系统来处理并发。

```rust
use actix_web::{web, App, HttpServer, HttpResponse, Responder};

async fn greet(name: web::Path<String>) -> impl Responder {
    format!("Hello {}!", name)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/hello/{name}", web::get().to(greet))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
```

**优势**：
- 极高的并发处理能力
- 成熟的生态和丰富的中间件
- 良好的文档和社区支持

**适用场景**：
- 高性能要求的API服务
- 需要极致并发处理的应用
- 对成熟度要求高的企业级项目

#### Axum：类型安全的现代选择
Axum由Tokio团队开发，深度整合tokio生态系统，基于tower中间件体系。

```rust
use axum::{
    routing::get,
    Router,
};

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/", get(|| async { "Hello, World!" }));

    axum::Server::bind(&"0.0.0.0:3000".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}
```

**核心特点**：
- 类型安全的路由系统
- 基于tower的中间件架构
- 优秀的错误处理设计
- 深度集成tokio生态系统

#### Rocket：开发体验优先
Rocket以其开发体验著称，提供了大量的编译时检查和便捷的宏。

```rust
#[macro_use] extern crate rocket;

#[get("/")]
fn index() -> &'static str {
    "Hello, world!"
}

#[launch]
fn rocket() -> _ {
    rocket::build().mount("/", routes![index])
}
```

**特色功能**：
- 宏驱动的路由定义
- 编译时代码生成和验证
- 内置的表单处理、JSON支持
- 简洁直观的API设计

### 框架选择建议

**选择Actix-web当**：
- 需要处理极高的并发连接
- 已有Actor模型或Actix生态系统经验
- 对性能有极致要求

**选择Axum当**：
- 需要与tokio生态系统深度集成
- 重视类型安全和编译时错误检查
- 希望构建可组合的中间件链

**选择Rocket当**：
- 追求快速原型开发
- 重视开发体验和代码简洁性
- 需要内置的请求验证和数据处理

## 第二部分：Axum框架详解

### 路由系统设计

Axum的路由系统充分利用了Rust的类型系统，提供编译时安全保障。

#### 基础路由定义

```rust
use axum::{
    Router,
    routing::{get, post, put, delete},
    extract::Path,
    Json,
};
use serde::{Deserialize, Serialize};

// 路由参数提取
async fn get_user(Path(user_id): Path<u64>) -> String {
    format!("Getting user {}", user_id)
}

// JSON请求体处理
#[derive(Deserialize)]
struct CreateUser {
    name: String,
    email: String,
}

async fn create_user(Json(payload): Json<CreateUser>) -> String {
    format!("Creating user: {} ({})", payload.name, payload.email)
}

// 构建路由器
let app = Router::new()
    .route("/users", post(create_user))
    .route("/users/:id", get(get_user).put(update_user).delete(delete_user))
    .route("/health", get(|| async { "OK" }));
```

#### 嵌套路由和分组

```rust
use axum::Router;

// 用户相关路由组
fn user_routes() -> Router {
    Router::new()
        .route("/", get(list_users).post(create_user))
        .route("/:id", get(get_user).put(update_user).delete(delete_user))
        .route("/:id/posts", get(get_user_posts))
}

// 文章相关路由组
fn post_routes() -> Router {
    Router::new()
        .route("/", get(list_posts).post(create_post))
        .route("/:id", get(get_post).put(update_post))
}

// 主路由组合
let api_routes = Router::new()
    .nest("/users", user_routes())
    .nest("/posts", post_routes());

let app = Router::new()
    .nest("/api", api_routes)
    .route("/", get(index));
```

### 中间件架构

Axum基于tower的中间件模型，提供了强大的可组合性。

#### 中间件基础

```rust
use tower_http::trace::TraceLayer;
use tower_http::cors::{CorsLayer, Any};
use axum::Router;

// 内置中间件
let app = Router::new()
    .route("/", get(|| async { "Hello" }))
    .layer(TraceLayer::new_for_http())  // 请求跟踪
    .layer(
        CorsLayer::new()
            .allow_origin(Any)  // CORS配置
            .allow_methods(Any)
            .allow_headers(Any)
    );
```

#### 自定义中间件

```rust
use axum::{
    middleware::{self, Next},
    response::Response,
    http::Request,
    extract::State,
};
use std::time::Instant;

// 计时中间件
async fn timing_middleware(
    req: Request<axum::body::Body>,
    next: Next<axum::body::Body>,
) -> Response {
    let start = Instant::now();
    let response = next.run(req).await;
    let duration = start.elapsed();
    
    println!("请求处理耗时: {:?}", duration);
    response
}

// 认证中间件
async fn auth_middleware(
    State(state): State<AppState>,
    req: Request<axum::body::Body>,
    next: Next<axum::body::Body>,
) -> Result<Response, StatusCode> {
    // 从请求头提取token
    let token = req.headers()
        .get("Authorization")
        .and_then(|auth| auth.to_str().ok())
        .and_then(|auth| auth.strip_prefix("Bearer "))
        .ok_or(StatusCode::UNAUTHORIZED)?;
    
    // 验证token
    let user = verify_token(&state.secret_key, token)
        .map_err(|_| StatusCode::UNAUTHORIZED)?;
    
    // 将用户信息添加到扩展
    let mut req = req;
    req.extensions_mut().insert(user);
    
    Ok(next.run(req).await)
}
```

#### 中间件组合

```rust
use tower::ServiceBuilder;
use tower_http::trace::TraceLayer;

let middleware_stack = ServiceBuilder::new()
    .layer(TraceLayer::new_for_http())
    .layer(
        CorsLayer::new()
            .allow_origin("http://localhost:3000".parse().unwrap())
    )
    .layer(middleware::from_fn(auth_middleware))
    .layer(middleware::from_fn(timing_middleware));

let app = Router::new()
    .route("/protected", get(protected_route))
    .layer(middleware_stack);
```

### 状态管理

Axum提供了多种状态管理方式，适应不同的应用场景。

#### 共享状态

```rust
use axum::{
    Router,
    extract::State,
    routing::get,
};
use std::sync::Arc;
use tokio::sync::RwLock;

// 应用状态结构
#[derive(Clone)]
struct AppState {
    db: Arc<RwLock<Database>>,
    config: Arc<Config>,
    cache: Arc<RwLock<Cache>>,
}

impl AppState {
    fn new() -> Self {
        AppState {
            db: Arc::new(RwLock::new(Database::connect())),
            config: Arc::new(Config::load()),
            cache: Arc::new(RwLock::new(Cache::new())),
        }
    }
}

// 在处理器中使用状态
async fn get_user(
    State(state): State<AppState>,
    Path(user_id): Path<u64>,
) -> Result<Json<User>, AppError> {
    let db = state.db.read().await;
    let user = db.get_user(user_id).await?;
    Ok(Json(user))
}

// 构建应用
let state = AppState::new();
let app = Router::new()
    .route("/users/:id", get(get_user))
    .with_state(state);
```

#### 依赖注入模式

```rust
use axum::extract::FromRef;

// 定义可提取的服务
trait UserService: Send + Sync + 'static {
    async fn get_user(&self, id: u64) -> Result<User, AppError>;
    async fn create_user(&self, user: NewUser) -> Result<User, AppError>;
}

// 实现具体的服务
struct PostgresUserService {
    pool: PgPool,
}

impl UserService for PostgresUserService {
    async fn get_user(&self, id: u64) -> Result<User, AppError> {
        sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
            .fetch_one(&self.pool)
            .await
            .map_err(|e| AppError::Database(e))
    }
}

// 应用状态包含所有服务
#[derive(Clone, FromRef)]
struct AppState {
    user_service: Arc<dyn UserService>,
    post_service: Arc<dyn PostService>,
    auth_service: Arc<dyn AuthService>,
}
```

### 错误处理

Axum提供了优雅的错误处理机制，结合Rust的Result类型。

#### 自定义错误类型

```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;

#[derive(Debug)]
enum AppError {
    NotFound(String),
    Unauthorized,
    BadRequest(String),
    Internal(anyhow::Error),
    Database(sqlx::Error),
    Validation(Vec<String>),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error_message) = match self {
            AppError::NotFound(msg) => (StatusCode::NOT_FOUND, msg),
            AppError::Unauthorized => (
                StatusCode::UNAUTHORIZED,
                "未授权访问".to_string()
            ),
            AppError::BadRequest(msg) => (StatusCode::BAD_REQUEST, msg),
            AppError::Internal(err) => {
                eprintln!("内部错误: {:?}", err);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "服务器内部错误".to_string()
                )
            }
            AppError::Database(err) => {
                eprintln!("数据库错误: {:?}", err);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "数据库操作失败".to_string()
                )
            }
            AppError::Validation(errors) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                errors.join(", ")
            ),
        };

        let body = Json(json!({
            "error": error_message,
            "status": status.as_u16(),
        }));

        (status, body).into_response()
    }
}

// 从其他错误类型转换
impl From<sqlx::Error> for AppError {
    fn from(err: sqlx::Error) -> Self {
        AppError::Database(err)
    }
}

impl From<anyhow::Error> for AppError {
    fn from(err: anyhow::Error) -> Self {
        AppError::Internal(err)
    }
}
```

#### 统一的错误处理中间件

```rust
use axum::middleware;

async fn error_handling_middleware(
    req: Request<Body>,
    next: Next<Body>,
) -> Result<Response, AppError> {
    match next.run(req).await {
        Ok(response) => Ok(response),
        Err(err) => Err(err),
    }
}
```

## 第三部分：数据库集成

### SQLx：编译时验证的异步SQL

SQLx是Rust中最流行的异步数据库库，提供编译时SQL查询验证。

#### 配置和连接

```rust
use sqlx::postgres::{PgPool, PgPoolOptions};
use std::time::Duration;

async fn create_pool() -> Result<PgPool, sqlx::Error> {
    let database_url = std::env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");

    PgPoolOptions::new()
        .max_connections(20)
        .min_connections(5)
        .acquire_timeout(Duration::from_secs(3))
        .idle_timeout(Duration::from_secs(600))
        .max_lifetime(Duration::from_secs(1800))
        .connect(&database_url)
        .await
}
```

#### 查询构建和执行

```rust
use sqlx::{FromRow, query_as, query};
use chrono::{DateTime, Utc};

#[derive(Debug, FromRow, Serialize)]
struct User {
    id: i64,
    name: String,
    email: String,
    created_at: DateTime<Utc>,
    updated_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Deserialize)]
struct CreateUser {
    name: String,
    email: String,
}

// 编译时验证的查询
async fn get_users(pool: &PgPool) -> Result<Vec<User>, sqlx::Error> {
    sqlx::query_as!(
        User,
        "SELECT id, name, email, created_at, updated_at FROM users ORDER BY created_at DESC"
    )
    .fetch_all(pool)
    .await
}

// 带参数的查询
async fn find_user_by_email(
    pool: &PgPool,
    email: &str,
) -> Result<Option<User>, sqlx::Error> {
    sqlx::query_as!(
        User,
        "SELECT * FROM users WHERE email = $1",
        email
    )
    .fetch_optional(pool)
    .await
}

// 插入数据并返回ID
async fn create_user(
    pool: &PgPool,
    new_user: CreateUser,
) -> Result<User, sqlx::Error> {
    sqlx::query_as!(
        User,
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *",
        new_user.name,
        new_user.email
    )
    .fetch_one(pool)
    .await
}
```

#### 事务处理

```rust
use sqlx::PgConnection;

async fn transfer_funds(
    conn: &mut PgConnection,
    from_id: i64,
    to_id: i64,
    amount: f64,
) -> Result<(), sqlx::Error> {
    let mut tx = conn.begin().await?;
    
    // 扣减发送方余额
    sqlx::query!("UPDATE accounts SET balance = balance - $1 WHERE id = $2", amount, from_id)
        .execute(&mut *tx)
        .await?;
    
    // 增加接收方余额
    sqlx::query!("UPDATE accounts SET balance = balance + $1 WHERE id = $2", amount, to_id)
        .execute(&mut *tx)
        .await?;
    
    // 提交事务
    tx.commit().await?;
    
    Ok(())
}
```

#### 数据库迁移

```rust
use sqlx::migrate::Migrator;

static MIGRATOR: Migrator = sqlx::migrate!("./migrations");

async fn run_migrations(pool: &PgPool) -> Result<(), sqlx::migrate::MigrateError> {
    MIGRATOR.run(pool).await
}
```

### Diesel：类型安全的ORM

Diesel是Rust最成熟的ORM，提供强大的类型安全查询构建。

#### 模型定义

```rust
#[derive(Queryable, Selectable, Serialize, Deserialize)]
#[diesel(table_name = users)]
struct User {
    id: i32,
    name: String,
    email: String,
    created_at: chrono::NaiveDateTime,
}

#[derive(Insertable, Deserialize)]
#[diesel(table_name = users)]
struct NewUser {
    name: String,
    email: String,
}
```

#### 查询构建

```rust
use diesel::prelude::*;
use diesel::pg::PgConnection;

fn establish_connection() -> PgConnection {
    let database_url = std::env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");
    PgConnection::establish(&database_url)
        .expect("Error connecting to database")
}

fn get_users(conn: &mut PgConnection) -> QueryResult<Vec<User>> {
    users::table
        .select(User::as_select())
        .order(users::created_at.desc())
        .load(conn)
}

fn find_user_by_id(conn: &mut PgConnection, user_id: i32) -> QueryResult<User> {
    users::table
        .find(user_id)
        .select(User::as_select())
        .first(conn)
}

fn create_user(conn: &mut PgConnection, new_user: NewUser) -> QueryResult<User> {
    diesel::insert_into(users::table)
        .values(&new_user)
        .returning(User::as_returning())
        .get_result(conn)
}
```

### SeaORM：现代化的ORM

SeaORM是一个新的异步ORM，设计现代且易于使用。

#### 实体定义

```rust
use sea_orm::entity::prelude::*;

#[derive(Clone, Debug, PartialEq, DeriveEntityModel, Serialize, Deserialize)]
#[sea_orm(table_name = "users")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub name: String,
    pub email: String,
    pub created_at: DateTimeWithTimeZone,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {
    #[sea_orm(has_many = "super::post::Entity")]
    Post,
}

impl Related<super::post::Entity> for Entity {
    fn to() -> RelationDef {
        Relation::Post.def()
    }
}

impl ActiveModelBehavior for ActiveModel {}
```

#### 查询操作

```rust
use sea_orm::{DatabaseConnection, EntityTrait, QueryFilter, ColumnTrait};

async fn find_user_by_id(
    db: &DatabaseConnection,
    user_id: i32,
) -> Result<Option<user::Model>, sea_orm::DbErr> {
    user::Entity::find_by_id(user_id)
        .one(db)
        .await
}

async fn get_active_users(
    db: &DatabaseConnection,
) -> Result<Vec<user::Model>, sea_orm::DbErr> {
    user::Entity::find()
        .filter(user::Column::IsActive.eq(true))
        .all(db)
        .await
}
```

## 第四部分：序列化 - serde生态

### serde核心概念

serde是Rust生态系统中的序列化/反序列化框架，支持JSON、YAML、TOML、MessagePack等多种格式。

#### 基础序列化/反序列化

```rust
use serde::{Serialize, Deserialize};
use serde_json;

#[derive(Serialize, Deserialize, Debug)]
struct User {
    id: u64,
    name: String,
    email: String,
    #[serde(rename = "createdAt")]
    created_at: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    updated_at: Option<String>,
}

// 序列化为JSON
fn serialize_user(user: &User) -> Result<String, serde_json::Error> {
    serde_json::to_string(user)
}

// 从JSON反序列化
fn deserialize_user(json: &str) -> Result<User, serde_json::Error> {
    serde_json::from_str(json)
}

// 带格式化的JSON输出
fn to_pretty_json(user: &User) -> Result<String, serde_json::Error> {
    serde_json::to_string_pretty(user)
}
```

#### 高级特性

```rust
#[derive(Serialize, Deserialize, Debug)]
struct ApiResponse<T> {
    success: bool,
    data: Option<T>,
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    meta: Option<PaginationMeta>,
}

#[derive(Serialize, Deserialize, Debug)]
struct PaginationMeta {
    total: u64,
    page: u64,
    per_page: u64,
    total_pages: u64,
}

// 自定义序列化器
mod date_format {
    use chrono::{DateTime, Utc, NaiveDateTime};
    use serde::{self, Deserialize, Serializer, Deserializer};

    const FORMAT: &'static str = "%Y-%m-%d %H:%M:%S";

    pub fn serialize<S>(
        date: &DateTime<Utc>,
        serializer: S,
    ) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let s = format!("{}", date.format(FORMAT));
        serializer.serialize_str(&s)
    }

    pub fn deserialize<'de, D>(
        deserializer: D,
    ) -> Result<DateTime<Utc>, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        let dt = NaiveDateTime::parse_from_str(&s, FORMAT)
            .map_err(serde::de::Error::custom)?;
        Ok(DateTime::from_naive_utc_and_offset(dt, Utc))
    }
}

#[derive(Serialize, Deserialize)]
struct Event {
    #[serde(with = "date_format")]
    timestamp: DateTime<Utc>,
    // 其他字段...
}
```

#### 条件序列化

```rust
#[derive(Serialize, Deserialize)]
struct UserDetail {
    id: u64,
    name: String,
    email: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    phone: Option<String>,
    #[serde(skip_serializing)]
    password_hash: String,
    #[serde(default)]
    is_active: bool,
    #[serde(rename = "role", deserialize_with = "deserialize_role")]
    user_role: UserRole,
}

fn deserialize_role<'de, D>(deserializer: D) -> Result<UserRole, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let s: String = Deserialize::deserialize(deserializer)?;
    match s.as_str() {
        "admin" => Ok(UserRole::Admin),
        "user" => Ok(UserRole::User),
        _ => Err(serde::de::Error::custom("Invalid role")),
    }
}
```

### 与Web框架集成

```rust
use axum::{
    extract::Json,
    response::IntoResponse,
    http::StatusCode,
};

// 提取JSON请求体
async fn create_user(
    Json(payload): Json<CreateUserRequest>,
) -> Result<Json<UserResponse>, AppError> {
    // 处理逻辑...
    Ok(Json(UserResponse { ... }))
}

// 返回JSON响应
async fn get_users() -> impl IntoResponse {
    let users = vec![...];
    (StatusCode::OK, Json(users))
}

// 处理多格式请求
async fn handle_content_negotiation(
    accept: HeaderValue,
    data: MyData,
) -> Response {
    if accept.to_str().unwrap_or("").contains("application/json") {
        Json(data).into_response()
    } else if accept.to_str().unwrap_or("").contains("application/xml") {
        // 转换为XML
        Xml(data).into_response()
    } else {
        StatusCode::NOT_ACCEPTABLE.into_response()
    }
}
```

## 第五部分：认证与授权

### JWT认证实现

#### JWT工具库

```rust
use jsonwebtoken::{encode, decode, Header, Algorithm, Validation, EncodingKey, DecodingKey};
use serde::{Deserialize, Serialize};
use chrono::{Utc, Duration};

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    email: String,
    role: String,
    exp: usize,
    iat: usize,
}

struct JwtService {
    secret_key: String,
    expiration_hours: i64,
}

impl JwtService {
    fn new(secret_key: String, expiration_hours: i64) -> Self {
        JwtService {
            secret_key,
            expiration_hours,
        }
    }

    fn generate_token(&self, user: &User) -> Result<String, jsonwebtoken::errors::Error> {
        let now = Utc::now();
        let claims = Claims {
            sub: user.id.to_string(),
            email: user.email.clone(),
            role: user.role.to_string(),
            exp: (now + Duration::hours(self.expiration_hours)).timestamp() as usize,
            iat: now.timestamp() as usize,
        };

        encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(self.secret_key.as_bytes()),
        )
    }

    fn validate_token(&self, token: &str) -> Result<Claims, jsonwebtoken::errors::Error> {
        let mut validation = Validation::new(Algorithm::HS256);
        validation.set_required_spec_claims(&["exp", "sub"]);

        let token_data = decode::<Claims>(
            token,
            &DecodingKey::from_secret(self.secret_key.as_bytes()),
            &validation,
        )?;

        Ok(token_data.claims)
    }
}
```

#### 认证中间件

```rust
use axum::{
    extract::Request,
    middleware::Next,
    response::Response,
    http::StatusCode,
    extract::State,
};
use tower_http::auth::AsyncAuthorizeRequest;

#[derive(Clone)]
struct JwtAuth {
    jwt_service: JwtService,
}

impl<S> AsyncAuthorizeRequest<S> for JwtAuth
where
    S: Send + Sync,
{
    type RequestBody = axum::body::Body;
    type ResponseBody = axum::body::Body;
    type Future = std::pin::Pin<Box<dyn std::future::Future<Output = Result<Request, Response>> + Send>>;

    fn authorize(&mut self, request: Request<Self::RequestBody>) -> Self::Future {
        let jwt_service = self.jwt_service.clone();

        Box::pin(async move {
            // 从请求头提取token
            let token = request.headers()
                .get("Authorization")
                .and_then(|auth| auth.to_str().ok())
                .and_then(|auth| auth.strip_prefix("Bearer "))
                .ok_or_else(|| {
                    Response::builder()
                        .status(StatusCode::UNAUTHORIZED)
                        .body(axum::body::Body::empty())
                        .unwrap()
                })?;

            // 验证token
            let claims = jwt_service.validate_token(token)
                .map_err(|_| {
                    Response::builder()
                        .status(StatusCode::UNAUTHORIZED)
                        .body(axum::body::Body::from("Invalid token"))
                        .unwrap()
                })?;

            // 将用户信息添加到请求扩展
            let mut request = request;
            request.extensions_mut().insert(claims);
            
            Ok(request)
        })
    }
}
```

### OAuth2集成

#### OAuth2客户端实现

```rust
use oauth2::{
    AuthorizationCode, AuthUrl, ClientId, ClientSecret, CsrfToken, 
    RedirectUrl, Scope, TokenUrl, TokenResponse, Client,
    reqwest::async_http_client,
};
use url::Url;

#[derive(Clone)]
struct OAuth2Service {
    client: Client<oauth2::StandardErrorResponse<oauth2::BasicErrorResponseType>,
                   oauth2::StandardTokenResponse<oauth2::BasicTokenType>,
                   oauth2::BasicTokenType>,
}

impl OAuth2Service {
    fn new(client_id: &str, client_secret: &str, redirect_url: &str) -> Self {
        let auth_url = AuthUrl::new("https://accounts.google.com/o/oauth2/auth".to_string())
            .expect("Invalid authorization endpoint URL");
        let token_url = TokenUrl::new("https://www.googleapis.com/oauth2/v3/token".to_string())
            .expect("Invalid token endpoint URL");

        let client = Client::new(
            ClientId::new(client_id.to_string()),
        )
        .set_client_secret(ClientSecret::new(client_secret.to_string()))
        .set_auth_uri(auth_url)
        .set_token_uri(token_url)
        .set_redirect_uri(RedirectUrl::new(redirect_url.to_string())
            .expect("Invalid redirect URL"));

        OAuth2Service { client }
    }

    fn get_authorization_url(&self) -> (Url, CsrfToken) {
        self.client
            .authorize_url(CsrfToken::new_random)
            .add_scope(Scope::new("openid".to_string()))
            .add_scope(Scope::new("profile".to_string()))
            .add_scope(Scope::new("email".to_string()))
            .url()
    }

    async fn exchange_code(&self, code: &str) -> Result<String, oauth2::reqwest::Error<reqwest::Error>> {
        let token_result = self.client
            .exchange_code(AuthorizationCode::new(code.to_string()))
            .request_async(async_http_client)
            .await?;

        Ok(token_result.access_token().secret().clone())
    }
}
```

#### OAuth2回调处理

```rust
use axum::{
    extract::{Query, State},
    response::Redirect,
    Router,
    routing::get,
};

#[derive(Deserialize)]
struct AuthCallback {
    code: String,
    state: String,
}

async fn auth_callback(
    State(state): State<AppState>,
    Query(params): Query<AuthCallback>,
) -> Result<Redirect, AppError> {
    // 验证CSRF token
    if params.state != state.csrf_token {
        return Err(AppError::BadRequest("Invalid CSRF token".to_string()));
    }

    // 交换授权码获取access token
    let access_token = state.oauth2_service
        .exchange_code(&params.code)
        .await
        .map_err(|_| AppError::Internal(anyhow::anyhow!("Failed to exchange code")))?;

    // 使用access token获取用户信息
    let user_info = get_user_info(&access_token).await?;
    
    // 创建或更新用户
    let user = state.user_service
        .create_or_update_oauth_user(user_info)
        .await?;

    // 生成JWT token
    let jwt_token = state.jwt_service.generate_token(&user)?;

    // 重定向到前端，携带token
    Ok(Redirect::to(&format!(
        "/auth/success?token={}",
        jwt_token
    )))
}
```

## 第六部分：异步运行时 - tokio深度

### tokio核心概念

#### 运行时配置

```rust
use tokio::runtime::Builder;
use std::time::Duration;

fn create_runtime() -> tokio::runtime::Runtime {
    Builder::new_multi_thread()
        .worker_threads(4)  // 工作线程数
        .max_blocking_threads(512)  // 阻塞线程池大小
        .enable_all()  // 启用所有运行时特性
        .thread_name("my-app-worker")
        .thread_stack_size(3 * 1024 * 1024)  // 线程栈大小
        .global_queue_interval(61)  // 全局队列检查间隔
        .event_interval(61)  // 事件检查间隔
        .build()
        .unwrap()
}
```

#### 任务调度和执行

```rust
use tokio::task;
use std::sync::Arc;
use tokio::sync::Semaphore;

async fn process_batch(items: Vec<Item>) -> Vec<Result<Output, Error>> {
    let semaphore = Arc::new(Semaphore::new(10));  // 并发限制
    let mut handles = Vec::new();

    for item in items {
        let permit = semaphore.clone().acquire_owned().await.unwrap();
        
        let handle = task::spawn(async move {
            let result = process_item(item).await;
            drop(permit);  // 释放信号量
            result
        });
        
        handles.push(handle);
    }

    let mut results = Vec::with_capacity(handles.len());
    for handle in handles {
        results.push(handle.await.unwrap());
    }

    results
}
```

### 性能优化技巧

#### 避免阻塞异步运行时

```rust
use tokio::task;

// 错误的阻塞调用方式
async fn bad_blocking_operation() {
    std::thread::sleep(Duration::from_secs(1));  // 会阻塞整个运行时
    println!("完成");
}

// 正确的阻塞操作处理方式
async fn good_blocking_operation() {
    // 方式1：使用spawn_blocking
    let result = task::spawn_blocking(|| {
        // 在专门的阻塞线程中执行CPU密集型操作
        expensive_computation()
    }).await.unwrap();

    // 方式2：对于IO阻塞操作
    let file_content = task::spawn_blocking(|| {
        std::fs::read_to_string("large_file.txt")
    }).await.unwrap()?;
}
```

#### 通道和并发模式

```rust
use tokio::sync::{mpsc, oneshot, broadcast, watch};
use tokio::task;

// 生产者-消费者模式
async fn producer_consumer_pattern() {
    let (tx, mut rx) = mpsc::channel(100);
    
    // 生产者任务
    let producer = task::spawn(async move {
        for i in 0..100 {
            tx.send(i).await.unwrap();
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    });
    
    // 消费者任务
    let consumer = task::spawn(async move {
        while let Some(value) = rx.recv().await {
            println!("收到: {}", value);
            // 处理值
        }
    });
    
    // 等待任务完成
    producer.await.unwrap();
    consumer.await.unwrap();
}

// 请求-响应模式
async fn request_response_pattern() {
    let (tx, rx) = oneshot::channel();
    
    // 模拟异步请求
    task::spawn(async move {
        // 一些异步操作
        tokio::time::sleep(Duration::from_secs(1)).await;
        let result =
```

## 相关术语

[[Rust系统编程入门到精通]]、[[Rust编程基础]]、[[Flutter跨平台开发实战]]、[[Go语言核心]]、[[Go语言系统编程指南]]、[[Python全栈开发教程]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
